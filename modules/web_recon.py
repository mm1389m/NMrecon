"""
NightMare Recon — modules/web_recon.py
Web recon: HTTP probe, tech fingerprint, security headers,
SSL/TLS, WAF, email harvest, robots.txt, Wayback URLs.
Developed by mm1389m  |  v1.0.0
"""

import re
import ssl
import socket
import json
from datetime import datetime, timezone
from typing import Any

import requests
from requests.exceptions import RequestException

from core.banner import console, print_success, print_error, print_warning, print_info
from core.config import (
    DEFAULT_TIMEOUT, DEFAULT_USER_AGENT,
    TECH_SIGNATURES, WAF_SIGNATURES, SECURITY_HEADERS,
)
from utils.ui import print_kv_table, print_results_table, make_spinner, http_status_style

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_HEADERS = {
    "User-Agent":      DEFAULT_USER_AGENT,
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
}


def run_web_recon(
    domain:    str,
    wayback:   bool = True,
    ssl_check: bool = True,
) -> dict[str, Any]:
    print_info(f"Web recon  →  [bold white]{domain}[/bold white]")
    result: dict[str, Any] = {}

    print_info("  Probing HTTP/HTTPS...")
    http_data = _probe_http(domain)
    result.update(http_data)

    if "error" in http_data:
        print_error(f"HTTP probe failed: {http_data['error']}")
        return result
    else:
        _display_http_summary(http_data)

    print_info("  Checking robots.txt & sitemap.xml...")
    crawl = _check_crawl_files(domain)
    result["crawl_files"] = crawl
    for fname, info in crawl.items():
        if info.get("found"):
            console.print(f"    [bold bright_green]✔[/bold bright_green]  {fname}  "
                          f"({info.get('size', 0)} bytes)")
        else:
            console.print(f"    [dim]—  {fname}  not found[/dim]")

    if ssl_check:
        print_info("  SSL/TLS certificate inspection...")
        ssl_data = _get_ssl_cert(domain)
        result["ssl"] = ssl_data
        if ssl_data and "error" not in ssl_data:
            print_kv_table("SSL Certificate", ssl_data)
        else:
            print_warning(f"  SSL: {ssl_data.get('error', 'n/a')}")

    if wayback:
        print_info("  Fetching Wayback Machine URLs...")
        wb = get_wayback_urls(domain, limit=300)
        result["wayback_urls"] = wb
        if wb:
            print_success(
                f"  Wayback  →  [bold bright_green]{len(wb)}[/bold bright_green] URLs"
            )
            print_results_table(
                f"Wayback URLs (first 25 of {len(wb)})",
                ["URL"],
                [[u] for u in wb[:25]],
            )
        else:
            print_warning("  No Wayback URLs found.")

    return result


def _probe_http(domain: str) -> dict[str, Any]:
    session = requests.Session()
    session.headers.update(_HEADERS)
    resp = None

    for scheme in ("https", "http"):
        try:
            resp = session.get(
                f"{scheme}://{domain}",
                timeout=DEFAULT_TIMEOUT,
                allow_redirects=True,
                verify=False,
            )
            break
        except RequestException:
            continue

    if resp is None:
        return {"error": f"Could not connect to {domain}"}

    headers = dict(resp.headers)
    body    = _safe_decode(resp.content)

    return {
        "url":              str(resp.url),
        "status_code":      resp.status_code,
        "server":           headers.get("Server", "—"),
        "x_powered_by":     headers.get("X-Powered-By", "—"),
        "content_type":     headers.get("Content-Type", "—"),
        "page_title":       _extract_title(body),
        "redirect_chain":   [str(r.url) for r in resp.history],
        "technologies":     _detect_technologies(headers, body),
        "waf":              _detect_waf(headers, body),
        "security_headers": _audit_security_headers(headers),
        "emails":           _harvest_emails(body),
    }


def _detect_technologies(headers: dict, body: str) -> list[str]:
    combined = (
        " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
        + " " + body[:60_000].lower()
    )
    found: list[str] = []
    for tech, sigs in TECH_SIGNATURES.items():
        if any(sig.lower() in combined for sig in sigs):
            if tech not in found:
                found.append(tech)
    return sorted(found)


def _detect_waf(headers: dict, body: str) -> str:
    combined = (
        " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
        + " " + body[:4000].lower()
    )
    for waf_name, sigs in WAF_SIGNATURES.items():
        if any(sig.lower() in combined for sig in sigs):
            return waf_name
    return "None detected"


def _audit_security_headers(headers: dict) -> dict[str, str]:
    h_lower = {k.lower(): v for k, v in headers.items()}
    return {
        header: h_lower.get(header.lower(), "MISSING")
        for header in SECURITY_HEADERS
    }


def _harvest_emails(body: str) -> list[str]:
    pattern = r"[a-zA-Z0-9._%+\-]{1,64}@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,10}"
    skip = {"example.com", "w3.org", "schema.org", "schemastuff.com"}
    return sorted({
        e for e in re.findall(pattern, body)
        if not any(s in e for s in skip) and len(e) < 100
    })


def _check_crawl_files(domain: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    paths = {"robots.txt": "/robots.txt", "sitemap.xml": "/sitemap.xml"}
    for fname, path in paths.items():
        entry: dict[str, Any] = {"found": False}
        for scheme in ("https", "http"):
            try:
                resp = requests.get(
                    f"{scheme}://{domain}{path}",
                    timeout=8, headers=_HEADERS, verify=False,
                )
                if resp.status_code == 200 and len(resp.text) > 10:
                    entry["found"]   = True
                    entry["url"]     = str(resp.url)
                    entry["size"]    = len(resp.content)
                    if fname == "robots.txt":
                        disallowed = re.findall(r"(?i)Disallow:\s*(.+)", resp.text)
                        entry["disallowed_paths"] = [d.strip() for d in disallowed if d.strip()]
                    if fname == "sitemap.xml":
                        entry["url_count"] = len(re.findall(r"<loc>([^<]+)</loc>", resp.text))
                    break
            except RequestException:
                continue
        result[fname] = entry
    return result


def _get_ssl_cert(domain: str, port: int = 443) -> dict[str, Any]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode    = ssl.CERT_NONE
    try:
        with socket.create_connection((domain, port), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert    = ssock.getpeercert()
                cipher  = ssock.cipher()
                tls_ver = ssock.version()
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        return {"error": f"Cannot reach {domain}:{port} — {exc}"}
    except ssl.SSLError as exc:
        return {"error": f"SSL error: {exc}"}

    if not cert:
        return {"error": "No certificate returned"}

    subject   = dict(x[0] for x in cert.get("subject", []))
    issuer    = dict(x[0] for x in cert.get("issuer", []))
    not_after = cert.get("notAfter", "")
    sans      = [v for _, v in cert.get("subjectAltName", [])]

    days_left  = None
    expiry_str = not_after
    if not_after:
        try:
            exp = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            days_left  = (exp - datetime.now(timezone.utc)).days
            expiry_str = f"{not_after}  ({days_left}d remaining)"
        except ValueError:
            pass

    status = "—"
    if days_left is not None:
        status = (f"✔ VALID ({days_left}d)" if days_left > 0
                  else f"✘ EXPIRED ({abs(days_left)}d ago)")

    return {
        "Subject CN":   subject.get("commonName", "—"),
        "Issuer CN":    issuer.get("commonName",  "—"),
        "Issuer Org":   issuer.get("organizationName", "—"),
        "Not Before":   cert.get("notBefore", "—"),
        "Not After":    expiry_str,
        "Status":       status,
        "TLS Version":  tls_ver or "—",
        "Cipher Suite": cipher[0] if cipher else "—",
        "SANs":         sans,
    }


def get_wayback_urls(domain: str, limit: int = 300) -> list[str]:
    """Fetch archived URLs from Wayback Machine CDX API."""
    api_url = (
        "https://web.archive.org/cdx/search/cdx"
        f"?url=*.{domain}&output=json&fl=original"
        f"&collapse=urlkey&limit={limit}"
    )
    try:
        with make_spinner(f"Fetching Wayback URLs for {domain}...") as sp:
            sp.add_task("wb", total=None)
            resp = requests.get(api_url, timeout=25, headers=_HEADERS)
        resp.raise_for_status()
        data = resp.json()
    except RequestException as exc:
        print_warning(f"Wayback API error: {exc}")
        return []
    except (json.JSONDecodeError, ValueError):
        print_warning("Wayback API returned invalid JSON.")
        return []

    if not data or len(data) < 2:
        return []

    urls: set[str] = set()
    for row in data[1:]:
        if row and isinstance(row, list) and len(row) > 0 and row[0]:
            urls.add(row[0])
    return sorted(urls)


def _display_http_summary(data: dict) -> None:
    code   = data.get("status_code", 0)
    url    = data.get("url", "—")
    server = data.get("server", "—")
    title  = data.get("page_title", "—")
    waf    = data.get("waf", "None detected")
    techs  = data.get("technologies", [])
    emails = data.get("emails", [])

    console.print()
    console.print(f"  [bold green]URL[/bold green]           {url}")
    console.print(f"  [bold green]Status[/bold green]        {http_status_style(code)}")
    console.print(f"  [bold green]Server[/bold green]        [white]{server}[/white]")
    console.print(f"  [bold green]Title[/bold green]         [white]{title}[/white]")

    waf_style = "bold yellow" if waf != "None detected" else "dim green"
    console.print(f"  [bold green]WAF[/bold green]           [{waf_style}]{waf}[/{waf_style}]")

    if techs:
        console.print(
            "  [bold green]Technologies[/bold green]  "
            + ",  ".join(f"[bright_green]{t}[/bright_green]" for t in techs)
        )
    if emails:
        console.print(
            "  [bold green]Emails[/bold green]        "
            + ",  ".join(f"[cyan]{e}[/cyan]" for e in emails[:6])
            + (f"  [dim]+{len(emails)-6} more[/dim]" if len(emails) > 6 else "")
        )
    console.print()

    sec = data.get("security_headers", {})
    if sec:
        from rich.table import Table
        from rich import box as rbox
        t = Table(
            title="[bold bright_green]Security Headers Audit[/bold bright_green]",
            box=rbox.SIMPLE_HEAD, border_style="dim green", header_style="bold green", expand=False,
        )
        t.add_column("Header", style="bold white", width=36, no_wrap=True)
        t.add_column("Value",  overflow="fold")
        for header, val in sec.items():
            disp = ("[bold red]✘  MISSING[/bold red]"
                    if val == "MISSING"
                    else f"[bold bright_green]✔[/bold bright_green]  [dim]{str(val)[:80]}[/dim]")
            t.add_row(header, disp)
        console.print(t)
        console.print()


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>([^<]{1,120})</title>", html, re.IGNORECASE)
    return m.group(1).strip() if m else "—"


def _safe_decode(content: bytes) -> str:
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return content.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return content.decode("utf-8", errors="replace")

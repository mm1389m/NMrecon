"""
NightMare Recon — modules/subdomain.py
Subdomain enumeration: crt.sh → subfinder → DNS brute-force.
Live-host check: httpx → requests fallback.
Developed by mm1389m  |  v1.0.0
"""

import shutil
import subprocess
import socket
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests
from requests.exceptions import RequestException

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn

from core.banner import console, print_success, print_error, print_warning, print_info
from core.config import SUBDOMAIN_WORDLIST, DEFAULT_TIMEOUT, DEFAULT_USER_AGENT
from utils.ui import print_results_table, make_spinner

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_LIVE_WORKERS = 30
_DNS_WORKERS  = 50
_REQ_HEADERS  = {"User-Agent": DEFAULT_USER_AGENT}


def run_subdomain_enum(
    domain:     str,
    brute:      bool = True,
    live_check: bool = True,
) -> list[str]:
    print_info(f"Subdomain enum  →  [bold white]{domain}[/bold white]")
    all_subs: set[str] = set()

    print_info("  Source: crt.sh (certificate transparency)")
    crt = _query_crtsh(domain)
    all_subs.update(crt)
    print_success(f"  crt.sh        →  {len(crt)} subdomains")

    if shutil.which("subfinder"):
        print_info("  Source: subfinder")
        sf = _run_subfinder(domain)
        new = sf - all_subs
        all_subs.update(sf)
        print_success(f"  subfinder     →  {len(sf)} total  ({len(new)} new)")
    else:
        print_warning("  subfinder not found — install via setup.sh for better results")

    if brute:
        print_info("  Source: DNS brute-force")
        bf = _dns_bruteforce(domain)
        new = bf - all_subs
        all_subs.update(bf)
        print_success(f"  brute-force   →  {len(bf)} total  ({len(new)} new)")

    sorted_subs = sorted(all_subs)
    print_success(
        f"Total unique subdomains: [bold bright_green]{len(sorted_subs)}[/bold bright_green]"
    )

    if not sorted_subs:
        print_warning("No subdomains discovered.")
        return []

    print_results_table(
        f"Subdomains ({len(sorted_subs)})",
        ["Subdomain"],
        [[s] for s in sorted_subs],
    )

    if live_check:
        print_info("  Running live-host check...")
        live = check_live(sorted_subs)
        if live:
            rows = [
                [h["host"], h["url"], str(h["status"]), str(h.get("title", ""))[:58]]
                for h in live
            ]
            print_results_table(
                f"Live Hosts ({len(live)})",
                ["Host", "URL", "Status", "Title"],
                rows,
            )
        else:
            print_warning("No live hosts responded.")

    return sorted_subs


def _query_crtsh(domain: str) -> set[str]:
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    try:
        with make_spinner("Querying crt.sh...") as sp:
            sp.add_task("q", total=None)
            resp = requests.get(url, timeout=25, headers=_REQ_HEADERS)
        resp.raise_for_status()
        data = resp.json()
    except RequestException as exc:
        print_warning(f"crt.sh error: {exc}")
        return set()
    except (json.JSONDecodeError, ValueError):
        print_warning("crt.sh returned invalid JSON.")
        return set()

    subs: set[str] = set()
    for entry in data:
        raw_name = entry.get("name_value", "")
        for part in raw_name.split("\n"):
            part = part.strip().lstrip("*.")
            if (
                part
                and (part.endswith(f".{domain}") or part == domain)
                and re.match(r"^[a-zA-Z0-9._-]+$", part)
            ):
                subs.add(part.lower())
    return subs


def _run_subfinder(domain: str) -> set[str]:
    try:
        proc = subprocess.run(
            ["subfinder", "-d", domain, "-silent", "-all"],
            capture_output=True, text=True, timeout=120,
        )
        return {
            line.strip().lower()
            for line in proc.stdout.splitlines()
            if line.strip()
            and domain in line.strip()
            and re.match(r"^[a-zA-Z0-9._-]+$", line.strip())
        }
    except subprocess.TimeoutExpired:
        print_warning("subfinder timed out (>120 s).")
        return set()
    except Exception as exc:
        print_warning(f"subfinder error: {exc}")
        return set()


def _resolve(subdomain: str) -> str | None:
    """Resolve a subdomain — socket.getaddrinfo() has NO timeout kwarg.
    Timeout is set globally before the pool starts."""
    try:
        info = socket.getaddrinfo(subdomain, None)
        if info:
            return subdomain
    except (socket.gaierror, OSError):
        pass
    except Exception:
        pass
    return None


def _dns_bruteforce(domain: str) -> set[str]:
    if not SUBDOMAIN_WORDLIST.exists():
        print_warning(f"Wordlist missing: {SUBDOMAIN_WORDLIST} — run ./setup.sh")
        return set()

    words = [
        w.strip()
        for w in SUBDOMAIN_WORDLIST.read_text(errors="replace").splitlines()
        if w.strip() and not w.startswith("#")
    ]
    candidates = [f"{w}.{domain}" for w in words]

    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(3.0)
    found: set[str] = set()

    try:
        with Progress(
            SpinnerColumn(spinner_name="dots2", style="bold bright_green"),
            TextColumn("[bold green]DNS brute-force[/bold green]"),
            BarColumn(bar_width=30, style="green", complete_style="bright_green"),
            MofNCompleteColumn(),
            console=console,
            transient=True,
        ) as prog:
            task = prog.add_task("brute", total=len(candidates))
            with ThreadPoolExecutor(max_workers=_DNS_WORKERS) as ex:
                futures = {ex.submit(_resolve, c): c for c in candidates}
                for fut in as_completed(futures):
                    prog.advance(task)
                    try:
                        res = fut.result()
                        if res:
                            found.add(res)
                    except Exception:
                        pass
    finally:
        socket.setdefaulttimeout(old_timeout)

    return found


def check_live(hosts: list[str]) -> list[dict[str, Any]]:
    if not hosts:
        return []
    if shutil.which("httpx"):
        result = _httpx_check(hosts)
        if result is not None:
            return result
    return _requests_check(hosts)


def _httpx_check(hosts: list[str]) -> list[dict[str, Any]] | None:
    try:
        proc = subprocess.run(
            ["httpx", "-silent", "-status-code", "-title", "-no-color",
             "-follow-redirects", "-timeout", "8"],
            input="\n".join(hosts),
            capture_output=True, text=True, timeout=180,
        )
        live: list[dict[str, Any]] = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            url   = parts[0] if parts else ""
            host  = url.replace("https://", "").replace("http://", "").rstrip("/")
            status = 0
            title  = ""
            for p in parts[1:]:
                if p.startswith("[") and p.endswith("]"):
                    inner = p[1:-1]
                    if inner.isdigit():
                        status = int(inner)
                    elif inner:
                        title = inner
            live.append({"host": host, "url": url, "status": status, "title": title})
        return live
    except subprocess.TimeoutExpired:
        print_warning("httpx timed out — falling back to requests.")
        return None
    except Exception as exc:
        print_warning(f"httpx failed ({exc}) — falling back to requests.")
        return None


def _probe_one(host: str) -> dict[str, Any] | None:
    for scheme in ("https", "http"):
        try:
            resp = requests.get(
                f"{scheme}://{host}",
                timeout=DEFAULT_TIMEOUT,
                headers=_REQ_HEADERS,
                allow_redirects=True,
                verify=False,
            )
            return {
                "host":   host,
                "url":    str(resp.url),
                "status": resp.status_code,
                "title":  _extract_title(resp.text),
                "server": resp.headers.get("Server", ""),
            }
        except RequestException:
            continue
    return None


def _requests_check(hosts: list[str]) -> list[dict[str, Any]]:
    live: list[dict[str, Any]] = []
    with Progress(
        SpinnerColumn(spinner_name="dots2", style="bold bright_green"),
        TextColumn("[bold green]Live check[/bold green]"),
        BarColumn(bar_width=30, style="green", complete_style="bright_green"),
        MofNCompleteColumn(),
        console=console,
        transient=True,
    ) as prog:
        task = prog.add_task("check", total=len(hosts))
        with ThreadPoolExecutor(max_workers=_LIVE_WORKERS) as ex:
            futures = {ex.submit(_probe_one, h): h for h in hosts}
            for fut in as_completed(futures):
                prog.advance(task)
                try:
                    res = fut.result()
                    if res:
                        live.append(res)
                except Exception:
                    pass
    return sorted(live, key=lambda x: x.get("status", 0))


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>([^<]{1,120})</title>", html, re.IGNORECASE)
    return m.group(1).strip() if m else ""

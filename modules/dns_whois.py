"""
NightMare Recon — modules/dns_whois.py
WHOIS lookup and full DNS enumeration with AXFR zone-transfer probe.
Developed by mm1389m  |  v1.0.0
"""

import subprocess
import shutil
from typing import Any

from rich.table import Table
from rich import box

from core.banner import console, print_success, print_error, print_warning, print_info
from core.config import DNS_RECORD_TYPES
from utils.ui import print_kv_table, make_spinner, print_results_table

try:
    import dns.resolver
    import dns.zone
    import dns.query
    import dns.exception
    _HAS_DNSPY = True
except ImportError:
    _HAS_DNSPY = False


def run_whois(domain: str) -> dict[str, Any]:
    if not shutil.which("whois"):
        print_warning("whois not installed  (apt install whois)")
        return {"error": "whois not installed"}

    print_info(f"WHOIS  →  [bold white]{domain}[/bold white]")
    try:
        with make_spinner(f"Querying WHOIS for {domain}") as sp:
            sp.add_task("w", total=None)
            proc = subprocess.run(
                ["whois", domain],
                capture_output=True, text=True, timeout=30,
            )
        raw = proc.stdout.strip()
        if not raw:
            print_warning("WHOIS returned empty response.")
            return {"note": "empty response"}
    except subprocess.TimeoutExpired:
        print_warning("WHOIS timed out (>30 s).")
        return {"error": "timeout"}
    except Exception as exc:
        print_error(f"WHOIS failed: {exc}")
        return {"error": str(exc)}

    parsed = _parse_whois(raw)
    if parsed:
        print_kv_table(f"WHOIS — {domain}", parsed)
    else:
        print_warning("Non-standard WHOIS format — showing raw snippet:")
        console.print(f"  [dim]{raw[:600]}[/dim]")

    return parsed if parsed else {"raw_snippet": raw[:1000]}


def _parse_whois(raw: str) -> dict[str, Any]:
    field_map: dict[str, list[str]] = {
        "Domain Name":        ["Domain Name:"],
        "Registrar":          ["Registrar:", "Registrar Name:"],
        "Registrar URL":      ["Registrar URL:"],
        "Registrant Name":    ["Registrant Name:"],
        "Registrant Org":     ["Registrant Organization:", "Registrant Org:"],
        "Registrant Country": ["Registrant Country:"],
        "Name Servers":       ["Name Server:"],
        "Created":            ["Creation Date:", "Created Date:", "created:"],
        "Updated":            ["Updated Date:", "Last Updated On:", "changed:"],
        "Expires":            ["Registry Expiry Date:", "Expiry Date:", "expires:"],
        "Status":             ["Domain Status:"],
        "DNSSEC":             ["DNSSEC:"],
        "Admin Email":        ["Admin Email:"],
    }

    parsed: dict[str, Any] = {}
    lines = raw.splitlines()

    for display_key, search_keys in field_map.items():
        values: list[str] = []
        for line in lines:
            stripped = line.strip()
            for sk in search_keys:
                if stripped.lower().startswith(sk.lower()):
                    val = stripped[len(sk):].strip()
                    if val and val not in values:
                        values.append(val)
        if not values:
            continue
        parsed[display_key] = values if display_key == "Name Servers" and len(values) > 1 else values[0]

    return parsed


def run_dns_enum(domain: str) -> dict[str, Any]:
    print_info(f"DNS enum  →  [bold white]{domain}[/bold white]")

    if _HAS_DNSPY:
        results = _dns_python_query(domain)
    else:
        print_warning("dnspython not installed — falling back to dig.")
        results = _dns_dig_query(domain)

    _display_dns_table(domain, results)

    if _HAS_DNSPY and "NS" in results:
        _attempt_zone_transfer(domain, results)

    return results


def _dns_python_query(domain: str) -> dict[str, list[str]]:
    resolver = dns.resolver.Resolver()
    resolver.timeout     = 5
    resolver.lifetime    = 12
    resolver.nameservers = ["8.8.8.8", "1.1.1.1", "8.8.4.4"]
    results: dict[str, list[str]] = {}

    for rtype in DNS_RECORD_TYPES:
        try:
            answers = resolver.resolve(domain, rtype)
            vals = [str(r) for r in answers]
            if vals:
                results[rtype] = vals
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer,
                dns.resolver.Timeout, dns.exception.DNSException):
            pass
        except Exception:
            pass

    return results


def _dns_dig_query(domain: str) -> dict[str, list[str]]:
    if not shutil.which("dig"):
        print_warning("dig not found — DNS enum unavailable.")
        return {"error": ["dig not installed"]}

    results: dict[str, list[str]] = {}
    for rtype in DNS_RECORD_TYPES:
        try:
            out = subprocess.run(
                ["dig", "+short", "+time=5", "+tries=1", domain, rtype, "@8.8.8.8"],
                capture_output=True, text=True, timeout=12,
            ).stdout.strip()
            if out:
                vals = [l.strip() for l in out.splitlines() if l.strip()]
                if vals:
                    results[rtype] = vals
        except Exception:
            pass

    return results


def _attempt_zone_transfer(domain: str, dns_results: dict) -> None:
    ns_list = dns_results.get("NS", [])
    if not ns_list:
        return

    print_info("  Attempting AXFR zone transfer...")
    found_any = False

    for ns_raw in ns_list[:4]:
        ns = ns_raw.rstrip(".")
        try:
            z = dns.zone.from_xfr(dns.query.xfr(ns, domain, timeout=8))
            records = [str(n) for n in z.nodes.keys()]
            if records:
                found_any = True
                print_warning(
                    f"  ZONE TRANSFER succeeded on [bold]{ns}[/bold]! "
                    f"{len(records)} records exposed."
                )
                print_results_table(
                    f"AXFR Records — {ns}",
                    ["Record Name"],
                    [[r] for r in records[:60]],
                )
        except Exception:
            pass

    if not found_any:
        print_success("  Zone transfer blocked on all NS servers.")


def _display_dns_table(domain: str, results: dict) -> None:
    if not results or list(results.keys()) == ["error"]:
        print_warning("No DNS records found.")
        return

    t = Table(
        title=f"[bold bright_green]DNS Records — {domain}[/bold bright_green]",
        box=box.SIMPLE_HEAD,
        border_style="dim green",
        header_style="bold green",
        expand=False,
    )
    t.add_column("Type",  style="bold bright_green", width=8,  no_wrap=True)
    t.add_column("Value", style="white",              overflow="fold")

    total = 0
    for rtype, values in results.items():
        if isinstance(values, list):
            for v in values:
                t.add_row(rtype, str(v))
                total += 1
        else:
            t.add_row(rtype, str(values))
            total += 1

    console.print()
    console.print(t)
    console.print()
    print_success(f"DNS enumeration complete — {total} record(s) found.")

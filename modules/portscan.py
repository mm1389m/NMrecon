"""
NightMare Recon — modules/portscan.py
Nmap-based port scanner — parses XML for reliable structured output.
Profiles: quick / standard / stealth / udp / vuln
Developed by mm1389m  |  v1.0.0
"""

import shutil
import subprocess
import xml.etree.ElementTree as ET
import tempfile
import os
from typing import Any

from rich.table import Table
from rich import box

from core.banner import console, print_success, print_error, print_warning, print_info
from core.config import NMAP_PROFILES, NMAP_TIMEOUT
from utils.ui import make_spinner

_PROFILE_DESC = {
    "quick":    "Top 100 ports, fast scan",
    "standard": "All ports + service/script detection",
    "stealth":  "SYN scan, fragmented (needs root)",
    "udp":      "Common UDP services (needs root)",
    "vuln":     "Vulnerability scripts on key ports",
}


def run_port_scan(target: str, profile: str = "quick") -> dict[str, Any]:
    if not shutil.which("nmap"):
        print_error("nmap not found — sudo apt install nmap")
        return {"error": "nmap not installed", "target": target, "ports": []}

    flags = NMAP_PROFILES.get(profile, NMAP_PROFILES["quick"])
    desc  = _PROFILE_DESC.get(profile, profile)

    print_info(
        f"Port scan  →  [bold white]{target}[/bold white]  "
        f"[dim](profile: {profile} — {desc})[/dim]"
    )

    xml_path: str | None = None
    try:
        fd, xml_path = tempfile.mkstemp(suffix=".xml", prefix="nmrecon_")
        os.close(fd)

        cmd = ["nmap"] + flags + ["-oX", xml_path, target]
        print_info(f"  cmd: [dim]{' '.join(cmd)}[/dim]")

        with make_spinner(f"Scanning {target} [{profile}]...") as sp:
            sp.add_task("scan", total=None)
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=NMAP_TIMEOUT.get(profile, 120),
            )

        if proc.returncode not in (0, 1):
            snippet = proc.stderr[:200].strip() if proc.stderr else ""
            print_warning(f"nmap exit code {proc.returncode}. {snippet}")

        result = _parse_nmap_xml(xml_path, target, profile)
        _display_port_table(target, result)
        return result

    except subprocess.TimeoutExpired:
        print_error(f"nmap timed out for profile '{profile}'. Try 'quick'.")
        return {"target": target, "profile": profile, "ports": [], "error": "timeout"}
    except PermissionError:
        print_error("nmap needs root for SYN/UDP. Try 'quick' or sudo.")
        return {"target": target, "profile": profile, "ports": [], "error": "permission denied"}
    except Exception as exc:
        print_error(f"Port scan failed: {exc}")
        return {"target": target, "profile": profile, "ports": [], "error": str(exc)}
    finally:
        if xml_path:
            try:
                os.unlink(xml_path)
            except OSError:
                pass


def _parse_nmap_xml(xml_path: str, target: str, profile: str) -> dict[str, Any]:
    try:
        tree = ET.parse(xml_path)
    except FileNotFoundError:
        print_warning("nmap did not produce XML output (scan may have been blocked).")
        return {"target": target, "profile": profile, "ports": []}
    except ET.ParseError as exc:
        print_warning(f"Could not parse nmap XML: {exc}")
        return {"target": target, "profile": profile, "ports": []}

    root     = tree.getroot()
    ports:   list[dict[str, str]] = []
    os_guess: str | None          = None

    for host in root.findall("host"):
        os_el = host.find("os")
        if os_el is not None:
            match = os_el.find("osmatch")
            if match is not None:
                os_guess = f"{match.get('name','')}  ({match.get('accuracy','')}% confidence)"

        ports_el = host.find("ports")
        if ports_el is None:
            continue

        for port_el in ports_el.findall("port"):
            state_el = port_el.find("state")
            if state_el is None:
                continue
            state = state_el.get("state", "")
            if state not in ("open", "filtered"):
                continue

            svc_el      = port_el.find("service")
            svc_name    = svc_el.get("name",      "") if svc_el is not None else ""
            svc_product = svc_el.get("product",   "") if svc_el is not None else ""
            svc_ver     = svc_el.get("version",   "") if svc_el is not None else ""
            svc_extra   = svc_el.get("extrainfo", "") if svc_el is not None else ""
            version_str = " ".join(filter(None, [svc_product, svc_ver, svc_extra])).strip()

            scripts = " | ".join(
                f"{s.get('id','')}: {s.get('output','').replace(chr(10),' ').strip()[:180]}"
                for s in port_el.findall("script")
                if s.get("output", "").strip()
            )

            ports.append({
                "port":    port_el.get("portid", ""),
                "proto":   port_el.get("protocol", "tcp"),
                "state":   state,
                "service": svc_name,
                "version": version_str,
                "scripts": scripts,
            })

    return {"target": target, "profile": profile, "ports": ports, "os_guess": os_guess}


def _display_port_table(target: str, result: dict) -> None:
    ports = result.get("ports", [])
    if not ports:
        print_warning("No open/filtered ports found.")
        return

    t = Table(
        title=f"[bold bright_green]Open Ports — {target}[/bold bright_green]",
        box=box.SIMPLE_HEAD,
        border_style="dim green",
        header_style="bold green",
        expand=False,
    )
    t.add_column("Port",    style="bold bright_green", width=8,  no_wrap=True)
    t.add_column("Proto",   style="dim green",          width=6,  no_wrap=True)
    t.add_column("State",   width=12, no_wrap=True)
    t.add_column("Service", style="bold white",         width=14, no_wrap=True)
    t.add_column("Version", style="green",              overflow="fold")

    for p in ports:
        state_str = (
            "[bold bright_green]open[/bold bright_green]"
            if p["state"] == "open"
            else "[bold yellow]filtered[/bold yellow]"
        )
        t.add_row(p["port"], p["proto"], state_str,
                  p["service"] or "unknown", p["version"] or "—")

    console.print()
    console.print(t)
    console.print()

    if result.get("os_guess"):
        console.print(f"  [dim green]OS guess:[/dim green]  [white]{result['os_guess']}[/white]")
        console.print()

    open_cnt = sum(1 for p in ports if p["state"] == "open")
    print_success(f"Port scan done — [bold bright_green]{open_cnt} open[/bold bright_green] port(s).")

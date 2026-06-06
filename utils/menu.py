"""
NightMare Recon — utils/menu.py
Interactive Rich-based menu system, all ask_* prompt helpers.
Developed by mm1389m  |  v1.0.0
"""

from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from core.banner import console
from utils.ui import divider

_MENU_ITEMS = [
    ("01", "Full Recon",        "Run all modules against a target domain"),
    ("02", "Subdomain Enum",    "Passive + brute-force subdomain discovery"),
    ("03", "DNS Lookup",        "Query A/AAAA/MX/NS/TXT/SOA/CAA records + AXFR"),
    ("04", "WHOIS Lookup",      "Domain registrar & ownership information"),
    ("05", "Port Scanner",      "Nmap scan with 5 configurable profiles"),
    ("06", "Web Recon",         "Headers, SSL, WAF, emails, robots.txt"),
    ("07", "Live Host Check",   "Concurrent HTTP/HTTPS host probing"),
    ("08", "Wayback URLs",      "Harvest historical URLs from Wayback Machine"),
    ("09", "IP Geolocation",    "Geolocate an IP address or domain"),
    ("10", "Tool Check",        "Show tool availability and install hints"),
    ("00", "Exit",              "Quit NightMare Recon"),
]

_PORT_PROFILES = {
    "1": ("quick",    "Top 100 ports, fast scan               (-T4 -F)"),
    "2": ("standard", "All ports, version + scripts           (-T4 -p- -sV -sC)"),
    "3": ("stealth",  "SYN scan, fragmented packets           (-T2 -sS -f)"),
    "4": ("udp",      "Common UDP services                    (-sU)"),
    "5": ("vuln",     "Vuln scripts on key ports              (--script=vuln)"),
}

_REPORT_FORMATS = {
    "1": "html",
    "2": "json",
    "3": "text",
    "4": "all",
}


def show_main_menu() -> str:
    console.print()
    divider()
    t = Table(box=box.SIMPLE, show_header=False, expand=False, padding=(0, 2), border_style="dim green")
    t.add_column("Key",  style="bold bright_green", width=5, no_wrap=True)
    t.add_column("Name", style="bold white",         width=22, no_wrap=True)
    t.add_column("Desc", style="dim green",          overflow="fold")

    for key, name, desc in _MENU_ITEMS:
        if key == "00":
            t.add_row()
            t.add_row(f"[bold red]{key}[/bold red]", f"[bold red]{name}[/bold red]", f"[dim]{desc}[/dim]")
        else:
            t.add_row(f"[bright_green]{key}[/bright_green]", name, desc)

    console.print(Panel(
        t,
        title="[bold bright_green]  ▓  NightMare Recon  ▓  [/bold bright_green]",
        border_style="green", expand=False, padding=(1, 2),
    ))
    console.print()

    valid = {item[0] for item in _MENU_ITEMS}
    while True:
        raw = Prompt.ask("  [bold bright_green]►[/bold bright_green] [bold white]Select option[/bold white]").strip()
        if raw.isdigit():
            raw = raw.zfill(2)
        if raw in valid:
            return raw
        console.print(f"  [yellow]!  Invalid: [bold]{raw}[/bold] — choose 00-10[/yellow]")


def ask_target(prompt: str = "Enter target domain") -> str:
    console.print()
    while True:
        val = Prompt.ask(
            f"  [bold bright_green]◉[/bold bright_green]  [bold white]{prompt}[/bold white]"
        ).strip()
        if val:
            return val
        console.print("  [yellow]!  Target cannot be empty.[/yellow]")


def ask_port_profile() -> str:
    console.print()
    t = Table(
        title="[bold bright_green]Port Scan Profiles[/bold bright_green]",
        box=box.SIMPLE_HEAD, border_style="dim green", header_style="bold green", expand=False,
    )
    t.add_column("#",       style="bold bright_green", width=4)
    t.add_column("Profile", style="bold white",         width=12)
    t.add_column("Details", style="dim green")
    for k, (name, desc) in _PORT_PROFILES.items():
        t.add_row(k, name, desc)
    console.print(t)

    while True:
        raw = Prompt.ask(
            "  [bold bright_green]►[/bold bright_green] [bold white]Select profile[/bold white]",
            default="1",
        ).strip()
        if raw in _PORT_PROFILES:
            return _PORT_PROFILES[raw][0]
        console.print(f"  [yellow]!  Enter 1-{len(_PORT_PROFILES)}[/yellow]")


def ask_full_recon_options() -> dict:
    console.print()
    console.print("  [dim green]Configure recon options (Enter = use default):[/dim green]")
    console.print()
    brute   = Confirm.ask("  [bold white]DNS brute-force?[/bold white]",  default=True)
    wayback = Confirm.ask("  [bold white]Wayback URLs?[/bold white]",      default=True)
    ssl     = Confirm.ask("  [bold white]SSL check?[/bold white]",         default=True)
    ports   = Confirm.ask("  [bold white]Port scan?[/bold white]",         default=True)
    profile = ask_port_profile() if ports else "quick"
    report  = Confirm.ask("  [bold white]Save report?[/bold white]",       default=True)
    return {
        "brute": brute, "wayback": wayback, "ssl": ssl,
        "portscan": ports, "port_profile": profile, "report": report,
    }


def ask_report_format() -> str:
    """Returns one of: html, json, text, all"""
    console.print()
    t = Table(
        title="[bold bright_green]Report Format[/bold bright_green]",
        box=box.SIMPLE, border_style="dim green", show_header=False, expand=False,
    )
    t.add_column("#",      style="bold bright_green", width=4)
    t.add_column("Format", style="bold white")
    for k, v in {"1": "HTML", "2": "JSON", "3": "Text", "4": "All formats"}.items():
        t.add_row(k, v)
    console.print(t)
    while True:
        raw = Prompt.ask(
            "  [bold bright_green]►[/bold bright_green] [bold white]Select format[/bold white]",
            default="4",
        ).strip()
        if raw in _REPORT_FORMATS:
            return _REPORT_FORMATS[raw]
        console.print("  [yellow]!  Enter 1-4[/yellow]")


def confirm_exit() -> bool:
    console.print()
    return Confirm.ask(
        "  [bold red]►[/bold red] [bold white]Exit NightMare Recon?[/bold white]",
        default=False,
    )

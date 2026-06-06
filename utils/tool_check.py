"""
NightMare Recon — utils/tool_check.py
Check system and Python tool availability.
Developed by mm1389m  |  v1.0.0
"""

import shutil
import importlib
from dataclasses import dataclass
from rich.table import Table
from rich import box
from core.banner import console


@dataclass
class _Tool:
    name: str
    binary: str | None
    required: bool
    purpose: str


_TOOLS: list[_Tool] = [
    _Tool("python3",     "python3",     True,  "Core runtime (3.9+)"),
    _Tool("nmap",        "nmap",        True,  "Port scanning"),
    _Tool("whois",       "whois",       True,  "WHOIS lookups"),
    _Tool("dig",         "dig",         True,  "DNS record queries"),
    _Tool("curl",        "curl",        True,  "HTTP testing"),
    _Tool("git",         "git",         True,  "Clone wordlists"),
    _Tool("rich",        None,          True,  "Terminal UI"),
    _Tool("requests",    None,          True,  "HTTP client"),
    _Tool("dnspython",   None,          False, "Pure-Python DNS (fallback: dig)"),
    _Tool("subfinder",   "subfinder",   False, "Passive subdomain enum"),
    _Tool("httpx",       "httpx",       False, "Fast live-host probing"),
    _Tool("waybackurls", "waybackurls", False, "Wayback URL harvest"),
    _Tool("ffuf",        "ffuf",        False, "Web fuzzer"),
    _Tool("amass",       "amass",       False, "Advanced OSINT enum"),
    _Tool("nuclei",      "nuclei",      False, "Template-based scanner"),
    _Tool("naabu",       "naabu",       False, "Fast port scanner"),
]


def _bin_ok(binary: str | None) -> bool:
    return bool(binary and shutil.which(binary))


def _lib_ok(name: str) -> bool:
    try:
        importlib.import_module(name.replace("-", "_"))
        return True
    except ImportError:
        return False


def run_tool_check() -> None:
    console.print()
    t = Table(
        title="[bold bright_green]  Tool Availability  [/bold bright_green]",
        box=box.SIMPLE_HEAD,
        border_style="dim green",
        header_style="bold green",
        expand=False,
        min_width=78,
    )
    t.add_column("Tool",    style="bold white",  width=14, no_wrap=True)
    t.add_column("Status",  width=16, no_wrap=True)
    t.add_column("Type",    style="dim",         width=12, no_wrap=True)
    t.add_column("Purpose", style="dim green",   overflow="fold")

    req_miss = opt_miss = 0
    for e in _TOOLS:
        ok = _lib_ok(e.name) if e.binary is None else _bin_ok(e.binary)
        status = ("[bold bright_green]✔  found[/bold bright_green]"
                  if ok else "[bold red]✘  missing[/bold red]")
        kind   = "[bold green]required[/bold green]" if e.required else "[dim]optional[/dim]"
        if not ok:
            req_miss += e.required
            opt_miss += not e.required
        t.add_row(e.name, status, kind, e.purpose)

    console.print(t)
    console.print()
    if req_miss == 0:
        console.print("  [bold bright_green]✔  All required tools present.[/bold bright_green]")
    else:
        console.print(f"  [bold red]✘  {req_miss} required tool(s) missing — run ./setup.sh[/bold red]")
    if opt_miss:
        console.print(f"  [dim yellow]ℹ  {opt_miss} optional tool(s) missing — built-in fallbacks active.[/dim yellow]")
    console.print()

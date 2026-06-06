"""
NightMare Recon — core/banner.py
Matrix-green banner, 0/1 rain animation, styled print helpers.
Developed by mm1389m  |  v1.0.0
"""

import time
import random
import sys
from rich.console import Console
from rich.rule import Rule

console = Console(highlight=False)

VERSION  = "1.0.0"
AUTHOR   = "mm1389m"

_ART = r"""
 ███╗   ██╗██╗ ██████╗ ██╗  ██╗████████╗███╗   ███╗ █████╗ ██████╗ ███████╗
 ████╗  ██║██║██╔════╝ ██║  ██║╚══██╔══╝████╗ ████║██╔══██╗██╔══██╗██╔════╝
 ██╔██╗ ██║██║██║  ███╗███████║   ██║   ██╔████╔██║███████║██████╔╝█████╗
 ██║╚██╗██║██║██║   ██║██╔══██║   ██║   ██║╚██╔╝██║██╔══██║██╔══██╗██╔══╝
 ██║ ╚████║██║╚██████╔╝██║  ██║   ██║   ██║ ╚═╝ ██║██║  ██║██║  ██║███████╗
 ╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝

 ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝"""


def _matrix_rain(rows: int = 5) -> None:
    width = min(getattr(console, "width", 80) or 80, 110)
    for row_idx in range(rows):
        parts = []
        density = 0.48 - row_idx * 0.06
        for _ in range(width):
            if random.random() < density:
                ch = random.choice("01")
                r = random.random()
                if r < 0.15:
                    parts.append(f"[bold bright_green]{ch}[/bold bright_green]")
                elif r < 0.45:
                    parts.append(f"[green]{ch}[/green]")
                else:
                    parts.append(f"[dim green]{ch}[/dim green]")
            else:
                parts.append(" ")
        console.print("".join(parts))
        time.sleep(0.05)


def _boot_sequence() -> None:
    msgs = [
        ("[dim green][ SYS  ][/dim green]", "Initialising NightMare engine..."),
        ("[dim green][ MOD  ][/dim green]", "Loading: dns  subdomain  ports  web  geo"),
        ("[dim green][ NET  ][/dim green]", "Verifying tool chain..."),
        ("[bold bright_green][ RDY  ][/bold bright_green]",
         "[bold white]System ready.[/bold white]"),
    ]
    for tag, msg in msgs:
        console.print(f"  {tag}  {msg}")
        time.sleep(0.09)
    console.print()


def print_banner(skip_animation: bool = False) -> None:
    console.print()
    if not skip_animation:
        _matrix_rain(rows=5)
        time.sleep(0.07)

    console.print(_ART, style="bold bright_green")
    console.print()
    console.print(
        f"  [bold bright_green]▓[/bold bright_green]  "
        f"[bold white]Professional Recon & Bug Bounty Toolkit[/bold white]  "
        f"[bold bright_green]▓[/bold bright_green]"
    )
    console.print(f"  [dim green]{'─' * 56}[/dim green]")
    console.print(
        f"  [dim green]Developed by {AUTHOR}[/dim green]"
        f"  [dim green]│[/dim green]  "
        f"[bold green]v{VERSION}[/bold green]"
        f"  [dim green]│[/dim green]  "
        f"[dim]github.com/{AUTHOR}/NMrecon[/dim]"
    )
    console.print()
    if not skip_animation:
        _boot_sequence()


def print_section(title: str) -> None:
    console.print()
    console.rule(
        f"[bold bright_green]  ▶  {title}  ◀  [/bold bright_green]",
        style="green",
    )
    console.print()


def print_success(msg: str) -> None:
    console.print(f"  [bold bright_green]✔[/bold bright_green]  {msg}")


def print_error(msg: str) -> None:
    console.print(f"  [bold red]✘[/bold red]  [red]{msg}[/red]")


def print_info(msg: str) -> None:
    console.print(f"  [bold green]▶[/bold green]  {msg}")


def print_warning(msg: str) -> None:
    console.print(f"  [bold yellow]![/bold yellow]  [yellow]{msg}[/yellow]")

"""
NightMare Recon — utils/ui.py
UI primitives: tables, progress bars, spinners, dividers.
Developed by mm1389m  |  v1.0.0
"""

from rich.table import Table
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn, TimeElapsedColumn, MofNCompleteColumn,
)
from rich import box
from core.banner import console


def divider(style: str = "dim green") -> None:
    console.rule(style=style)


def print_results_table(
    title: str,
    headers: list[str],
    rows: list[list],
    *,
    max_rows: int = 500,
) -> None:
    if not rows:
        console.print(f"  [dim]No results for: {title}[/dim]")
        return

    t = Table(
        title=f"[bold bright_green]{title}[/bold bright_green]",
        box=box.SIMPLE_HEAD,
        border_style="dim green",
        header_style="bold green",
        row_styles=["", "dim"],
        expand=False,
        min_width=50,
    )
    for i, h in enumerate(headers):
        if i == 0:
            t.add_column(h, style="bold white", no_wrap=True, min_width=22)
        else:
            t.add_column(h, style="bright_green")

    for row in rows[:max_rows]:
        t.add_row(*[str(c) for c in row])

    if len(rows) > max_rows:
        t.caption = f"[dim]... showing first {max_rows} of {len(rows)} results[/dim]"

    console.print()
    console.print(t)
    console.print()


def print_kv_table(title: str, data: dict) -> None:
    if not data:
        console.print(f"  [dim]No data: {title}[/dim]")
        return

    t = Table(
        title=f"[bold bright_green]{title}[/bold bright_green]",
        box=box.SIMPLE,
        border_style="dim green",
        show_header=False,
        expand=False,
        min_width=52,
    )
    t.add_column("Key",   style="bold green", no_wrap=True, min_width=26)
    t.add_column("Value", style="white",       overflow="fold")

    for k, v in data.items():
        if isinstance(v, list):
            val = "\n".join(str(x) for x in v) if v else "[dim]—[/dim]"
        elif v is None or v == "":
            val = "[dim]—[/dim]"
        else:
            val = str(v)
        t.add_row(str(k), val)

    console.print()
    console.print(t)
    console.print()


def make_progress(description: str = "Working") -> Progress:
    return Progress(
        SpinnerColumn(spinner_name="dots2", style="bold bright_green"),
        TextColumn(f"[bold green]{description}[/bold green]"),
        BarColumn(bar_width=32, style="green", complete_style="bright_green"),
        TaskProgressColumn(style="dim green"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )


def make_spinner(label: str = "Loading...") -> Progress:
    return Progress(
        SpinnerColumn(spinner_name="dots2", style="bold bright_green"),
        TextColumn(f"[bold green]{label}[/bold green]"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def http_status_style(code: int | str) -> str:
    try:
        c = int(code)
    except (TypeError, ValueError):
        return f"[dim]{code}[/dim]"
    if 200 <= c < 300:
        return f"[bold bright_green]{c}[/bold bright_green]"
    if 300 <= c < 400:
        return f"[bold cyan]{c}[/bold cyan]"
    if 400 <= c < 500:
        return f"[bold yellow]{c}[/bold yellow]"
    if c >= 500:
        return f"[bold red]{c}[/bold red]"
    return f"[dim]{c}[/dim]"

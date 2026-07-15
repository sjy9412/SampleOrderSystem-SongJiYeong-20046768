"""Rich 기반 콘솔 출력 유틸리티 (메인 앱 공용)."""
from __future__ import annotations

import sys
from typing import Any

if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    ctypes.windll.kernel32.SetConsoleCP(65001)
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text
from rich.panel import Panel

console = Console(highlight=False, force_terminal=True)

_STATUS_STYLES: dict[str, str] = {
    "RESERVED":  "bold yellow",
    "PRODUCING": "bold blue",
    "CONFIRMED": "bold green",
    "RELEASE":   "bold cyan",
    "REJECTED":  "bold red",
}


def _fmt_cell(key: str, value: Any) -> Text:
    if value is None:
        return Text("-", style="dim")
    s = str(value)
    if key == "status":
        style = _STATUS_STYLES.get(s, "")
        return Text(s, style=style)
    return Text(s)


def print_table(
    rows: list[dict],
    keys: list[str] | None = None,
    title: str = "",
    col_labels: dict[str, str] | None = None,
) -> None:
    if not rows:
        console.print("  [dim](데이터 없음)[/dim]")
        return
    cols = keys or list(rows[0].keys())
    labels = col_labels or {}
    t = Table(
        title=title or None,
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold white",
        border_style="bright_black",
        title_style="bold cyan",
        expand=False,
    )
    for col in cols:
        t.add_column(labels.get(col, col), no_wrap=True, overflow="ellipsis")
    for row in rows:
        t.add_row(*[_fmt_cell(k, row.get(k)) for k in cols])
    console.print(t)
    console.print(f"  [dim]{len(rows)}건[/dim]")


def show_menu_panel(title: str, items: list[tuple[str, str]]) -> None:
    """번호-설명 튜플 목록을 Panel 로 출력한다."""
    lines = []
    for num, label in items:
        if num == "0":
            lines.append(f"  [dim]{num}. {label}[/dim]")
        else:
            lines.append(f"  [bold]{num}.[/bold] {label}")
    console.print(Panel(
        "\n".join(lines),
        title=f"[bold cyan]{title}[/bold cyan]",
        border_style="bright_black",
        expand=False,
        padding=(0, 1),
    ))


def prompt_choice(label: str = "선택") -> str:
    console.print(f"\n  [bold cyan]{label} >[/bold cyan] ", end="")
    return input().strip()


def prompt_input(label: str) -> str:
    console.print(f"  [dim]{label}[/dim] ", end="")
    return input().strip()


def section(title: str) -> None:
    console.rule(f"[bold cyan]{title}[/bold cyan]", style="bright_black")


def success(msg: str) -> None:
    console.print(f"  [bold green]✓[/bold green] {msg}")


def error(msg: str) -> None:
    console.print(f"  [bold red]✗[/bold red] {msg}")


def info(msg: str) -> None:
    console.print(f"  [bold cyan]ℹ[/bold cyan] {msg}")


def warn(msg: str) -> None:
    console.print(f"  [bold yellow]⚠[/bold yellow] {msg}")

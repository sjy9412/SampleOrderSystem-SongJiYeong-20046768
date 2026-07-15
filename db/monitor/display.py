"""Rich 기반 콘솔 출력 유틸리티."""
from __future__ import annotations

import sys
from datetime import datetime
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

# UUID 앞 8자리만 표시 (가독성)
_UUID_LEN = 36


def _fmt(key: str, value: Any) -> Text:
    if value is None:
        return Text("null", style="dim")
    if isinstance(value, bool):
        return Text(str(value), style="bold green" if value else "bold red")

    s = str(value)

    # UUID 축약: xxxxxxxx-... → xxxx...
    if len(s) == _UUID_LEN and s.count("-") == 4:
        return Text(s[:8] + "…", style="dim cyan")

    # ISO datetime 축약: 2026-07-15T00:29:09.225857+00:00 → 07-15 00:29
    if len(s) >= 19 and "T" in s and s[4] == "-":
        try:
            dt = datetime.fromisoformat(s)
            return Text(dt.strftime("%m-%d %H:%M"), style="dim")
        except ValueError:
            pass

    return Text(s)


def print_table(rows: list[dict], keys: list[str] | None = None, title: str = ""):
    if not rows:
        console.print("  [dim](데이터 없음)[/dim]")
        return
    cols = keys or list(rows[0].keys())
    t = Table(
        title=title,
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold white",
        border_style="bright_black",
        title_style="bold cyan",
        expand=False,
    )
    for col in cols:
        t.add_column(col, no_wrap=True, overflow="ellipsis")
    for row in rows:
        t.add_row(*[_fmt(k, row.get(k)) for k in cols])
    console.print(t)
    console.print(f"  [dim]{len(rows)}건[/dim]")


def print_record(record: dict | None, title: str = ""):
    if record is None:
        console.print("  [bold red]레코드를 찾을 수 없습니다.[/bold red]")
        return
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1),
              border_style="bright_black", expand=False)
    t.add_column("key", style="dim", min_width=16)
    t.add_column("value", no_wrap=False)
    for k, v in record.items():
        # 레코드 상세에서는 UUID와 datetime을 전체 표시
        t.add_row(k, Text(str(v) if v is not None else "null"))
    if title:
        console.print(Panel(t, title=f"[bold cyan]{title}[/bold cyan]",
                            border_style="bright_black", expand=False))
    else:
        console.print(t)


def section(title: str):
    console.rule(f"[bold cyan]{title}[/bold cyan]", style="bright_black")


def success(msg: str): console.print(f"  [bold green]✓[/bold green] {msg}")
def error(msg: str):   console.print(f"  [bold red]✗[/bold red] {msg}")
def info(msg: str):    console.print(f"  [bold cyan]ℹ[/bold cyan] {msg}")
def warn(msg: str):    console.print(f"  [bold yellow]⚠[/bold yellow] {msg}")


def timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")

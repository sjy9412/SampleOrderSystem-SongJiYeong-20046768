"""cmd.Cmd 기반 읽기 전용 REPL."""
from __future__ import annotations

import cmd
import os
import sys
import time

from . import display as d
from .display import console
from .store import DataStore

BANNER = r"""
[bold cyan]
  ██████╗  █████╗ ████████╗ █████╗     ███╗   ███╗ ██████╗ ███╗   ██╗
  ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗    ████╗ ████║██╔═══██╗████╗  ██║
  ██║  ██║███████║   ██║   ███████║    ██╔████╔██║██║   ██║██╔██╗ ██║
  ██║  ██║██╔══██║   ██║   ██╔══██║    ██║╚██╔╝██║██║   ██║██║╚██╗██║
  ██████╔╝██║  ██║   ██║   ██║  ██║    ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║
  ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝    ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝[/bold cyan]
[dim]  실시간 JSON 데이터 모니터링 도구  v1.0.0  (Python)[/dim]
"""

HELP_TEXT = """
[bold cyan]DataMonitor — 사용 가능한 명령어[/bold cyan]
[bright_black]──────────────────────────────────────────────────────────[/bright_black]

[bold]조회[/bold]
  [yellow]list[/yellow]                           컬렉션 목록 및 레코드 수 출력
  [yellow]query[/yellow] <컬렉션>                 전체 레코드 조회
  [yellow]query[/yellow] <컬렉션> <필드>=<값>     필드값으로 필터링
  [yellow]get[/yellow] <컬렉션> <id>              ID로 단일 레코드 전체 조회
  [yellow]stats[/yellow]                          DB 파일 메타 및 컬렉션 통계

[bold]모니터링[/bold]
  [yellow]watch[/yellow] <컬렉션> [간격(초)]      주기적으로 파일을 읽어 테이블 갱신
                                 (기본 2초, [bold]q[/bold] Enter 또는 Ctrl+C 중지)

[bold]기타[/bold]
  [yellow]help[/yellow]                           이 도움말 출력
  [yellow]clear[/yellow]                          화면 지우기
  [yellow]exit[/yellow] / [yellow]quit[/yellow]   종료
"""

_CMDS = ["list", "query", "get", "stats", "watch", "help", "clear", "exit", "quit"]


class DataMonitorREPL(cmd.Cmd):
    use_rawinput = True

    def __init__(self, store: DataStore):
        super().__init__()
        self._store = store

    def cmdloop(self, intro=None):
        if intro:
            console.print(intro)
        stop = None
        while not stop:
            try:
                console.print("[bold cyan]dm>[/bold cyan] ", end="")
                line = input()
            except EOFError:
                line = "exit"
            except KeyboardInterrupt:
                console.print()
                continue
            stop = self.onecmd(self.precmd(line))
            stop = self.postcmd(stop, line)

    # ── 명령어 ───────────────────────────────────────────────────────────────

    def do_help(self, _):
        console.print(HELP_TEXT)

    def do_list(self, _):
        d.section("컬렉션 목록")
        d.print_table(self._store.stats())

    def do_query(self, arg: str):
        parts = arg.split(None, 1)
        if not parts:
            d.error("사용법: query <컬렉션> [필드=값]")
            return
        collection = parts[0]

        if len(parts) > 1 and "=" in parts[1]:
            field, _, value = parts[1].partition("=")
            rows = self._store.filter(collection, field.strip(), value.strip())
            d.section(f"{collection}  [{field.strip()}={value.strip()}]")
        else:
            rows = self._store.all(collection)
            d.section(collection)

        if rows is None:
            d.error(f"컬렉션 '{collection}'을 찾을 수 없습니다. list 로 확인하세요.")
            return
        d.print_table(rows)

    def do_get(self, arg: str):
        parts = arg.split(None, 1)
        if len(parts) < 2:
            d.error("사용법: get <컬렉션> <id>")
            return
        collection, record_id = parts[0], parts[1].strip()
        record = self._store.get_by_id(collection, record_id)
        d.print_record(record, title=f"{collection}  {record_id[:8]}…")

    def do_stats(self, _):
        d.section("DB 통계")
        meta = self._store.file_meta()
        console.print(f"  [dim]파일:[/dim]          {self._store.db_path()}")
        for k, v in meta.items():
            console.print(f"  [dim]{k:<16}[/dim] {v}")
        console.print()
        d.print_table(self._store.stats())

    def do_watch(self, arg: str):
        parts = arg.split()
        if not parts:
            d.error("사용법: watch <컬렉션> [간격(초)]")
            return
        collection = parts[0]
        try:
            interval = max(1.0, float(parts[1])) if len(parts) > 1 else 2.0
        except ValueError:
            interval = 2.0

        if self._store.all(collection) is None:
            d.error(f"컬렉션 '{collection}'을 찾을 수 없습니다.")
            return

        d.info(f"[bold]{collection}[/bold] 감시 시작 — {interval:.0f}초마다 파일 재읽기  "
               f"[dim](q Enter 또는 Ctrl+C 중지)[/dim]")

        def render():
            os.system("cls" if sys.platform == "win32" else "clear")
            console.print(
                f"\n  [bold cyan]WATCH[/bold cyan] [white]{collection}[/white] "
                f"[dim]{d.timestamp()}[/dim]  [dim](q Enter 중지)[/dim]"
            )
            d.print_table(self._store.all(collection) or [])

        render()
        try:
            while True:
                # interval 초 대기 중 입력이 들어오면 중단
                start = time.monotonic()
                while time.monotonic() - start < interval:
                    # Windows 에서 non-blocking 입력 확인
                    if sys.platform == "win32":
                        import msvcrt
                        if msvcrt.kbhit():
                            ch = msvcrt.getwche()
                            if ch in ("\r", "\n", "q", "Q"):
                                raise StopIteration
                    time.sleep(0.1)
                render()
        except (StopIteration, KeyboardInterrupt):
            pass

        os.system("cls" if sys.platform == "win32" else "clear")
        d.info(f"감시 중지 ({collection})")

    def do_clear(self, _):
        os.system("cls" if sys.platform == "win32" else "clear")
        console.print(BANNER)

    def do_exit(self, _):
        console.print("\n  [cyan]종료합니다. 안녕히 가세요![/cyan]\n")
        return True

    do_quit = do_exit

    def default(self, line: str):
        if line.strip():
            d.error(f"알 수 없는 명령어: '{line.split()[0]}'  (help 로 사용법 확인)")

    def completenames(self, text, *_):
        return [c for c in _CMDS if c.startswith(text)]

    def completedefault(self, text, *_):
        return [c for c in self._store.collections() if c.startswith(text)]


def run(db_path: str = "db.json"):
    store = DataStore(db_path)
    repl = DataMonitorREPL(store)
    console.print(BANNER)
    d.info(f"[dim]{db_path}[/dim] 연결됨")
    console.print("  [dim]help[/dim] 명령어로 사용법을 확인하세요.\n")
    try:
        repl.cmdloop()
    except KeyboardInterrupt:
        repl.do_exit("")

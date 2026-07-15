from __future__ import annotations
from datetime import datetime
from views.display import console, show_menu_panel, prompt_choice, separator, error, info, warn
from rich.panel import Panel
from rich.text import Text

BANNER = r"""[bold cyan]
  ███████╗ █████╗ ███╗   ███╗██████╗ ██╗     ███████╗
  ██╔════╝██╔══██╗████╗ ████║██╔══██╗██║     ██╔════╝
  ███████╗███████║██╔████╔██║██████╔╝██║     █████╗
  ╚════██║██╔══██║██║╚██╔╝██║██╔═══╝ ██║     ██╔══╝
  ███████║██║  ██║██║ ╚═╝ ██║██║     ███████╗███████╗
  ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚══════╝╚══════╝[/bold cyan]
[dim]  반도체 시료 생산주문 관리 시스템  v1.0.0[/dim]
"""


class MainController:

    def __init__(
        self,
        sub_controllers: list,
        *,
        sample_model=None,
        inventory_model=None,
        order_model=None,
        production_line=None,
    ) -> None:
        self._controllers = sub_controllers
        self._sample_model = sample_model
        self._inventory_model = inventory_model
        self._order_model = order_model
        self._production_line = production_line

    def _show_dashboard(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sample_count = len(self._sample_model.get_all()) if self._sample_model else 0
        total_stock  = (
            sum(r["quantity"] for r in self._inventory_model.get_all_stocks())
            if self._inventory_model else 0
        )
        order_count  = len(self._order_model.get_all()) if self._order_model else 0
        queue_count  = len(self._production_line.get_queue()) if self._production_line else 0

        body = (
            f"  등록 시료 [bold]{sample_count}종[/bold]   "
            f"총 재고 [bold]{total_stock}ea[/bold]   "
            f"전체 주문 [bold]{order_count}건[/bold]   "
            f"생산라인 [bold]{queue_count}건 대기[/bold]"
        )
        console.print(Panel(
            body,
            title=f"[bold white]시스템 현황[/bold white]  [dim]{now}[/dim]",
            border_style="bright_black",
            expand=False,
            padding=(0, 1),
        ))

    def run(self) -> None:
        console.print(BANNER)
        first = True
        while True:
            if not first:
                separator()
            first = False
            self._show_dashboard()
            console.print()
            show_menu_panel("메인 메뉴", [
                ("1", "시료 관리"),
                ("2", "시료 주문"),
                ("3", "주문 승인 / 거절"),
                ("4", "모니터링"),
                ("5", "생산라인 조회"),
                ("6", "출고 처리"),
                ("0", "종료"),
            ])
            choice = prompt_choice()
            if choice == "0":
                console.print("\n  [cyan]시스템을 종료합니다. 안녕히 가세요![/cyan]\n")
                break
            if choice.isdigit() and 1 <= int(choice) <= len(self._controllers):
                separator()
                self._controllers[int(choice) - 1].run()
            else:
                warn("잘못된 입력입니다.")

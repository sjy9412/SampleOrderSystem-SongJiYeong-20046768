from __future__ import annotations
from models.base import ModelEvent
from views.display import (
    console, print_table, show_menu_panel,
    prompt_choice, prompt_input, section,
    error, info, warn,
)
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text


class ProductionView:

    def __init__(self, model) -> None:
        model.subscribe(self)

    def show_menu(self) -> None:
        console.print()
        show_menu_panel("생산 라인", [
            ("1", "생산 현황 조회"),
            ("2", "대기 주문 목록"),
            ("0", "뒤로"),
        ])

    def get_menu_choice(self) -> str:
        return prompt_choice()

    def show_current(self, info_data: dict) -> None:
        section("현재 생산 현황")
        t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1),
                  border_style="bright_black", expand=False)
        t.add_column("항목", style="dim", min_width=16)
        t.add_column("값")
        t.add_row("주문 ID",      Text(info_data["order_id"], style="dim cyan"))
        t.add_row("시료명",       info_data["sample_name"])
        t.add_row("주문 수량",    str(info_data["quantity"]))
        t.add_row("실 생산량",    str(info_data["actual_qty"]))
        t.add_row("총 생산시간", f"{info_data['total_time']:.1f} min")
        console.print(Panel(t, title="[bold cyan]생산 중[/bold cyan]",
                            border_style="bright_black", expand=False))

    def show_no_current(self) -> None:
        info("현재 생산 중인 주문이 없습니다.")

    def show_queue(self, items: list[dict]) -> None:
        section("대기 주문 목록")
        if not items:
            info("대기 중인 주문이 없습니다.")
            return
        rows = [
            {
                "순번": str(item["position"]),
                "주문 ID": item["order_id"],
                "시료명": item["sample_name"],
                "고객명": item["customer_name"],
                "수량": f"{item['quantity']} ea",
            }
            for item in items
        ]
        print_table(rows)

    def show_error(self, message: str) -> None:
        error(message)

    def show_invalid_input(self) -> None:
        warn("잘못된 입력입니다.")

    def show_exit(self) -> None:
        info("뒤로 갑니다.")

    def get_title_input(self) -> str:
        return prompt_input("제목:")

    def get_id_input(self, action: str) -> str:
        return prompt_input(f"{action} ID:")

    def on_model_changed(self, event: ModelEvent) -> None:
        pass

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
        t.add_row("주문번호",     Text(info_data["order_no"], style="dim cyan"))
        t.add_row("시료명",       info_data["sample_name"])
        t.add_row("주문량",       f"{info_data['quantity']} ea")
        t.add_row("재고",         f"{info_data['stock']} ea")
        t.add_row("부족분",       f"{info_data['shortage']} ea")
        yield_pct = int(info_data["yield_rate"] * 100)
        t.add_row("실 생산량",    f"{info_data['actual_qty']} ea  (수율 {yield_pct}% / {info_data['avg_time']} min)")
        t.add_row("진행율",       f"{info_data['progress_pct']:.1f}%")
        t.add_row("완료 예정",    info_data["estimated_completion"])
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
                "주문번호": item["order_no"],
                "시료명": item["sample_name"],
                "주문량": f"{item['quantity']} ea",
                "부족분": f"{item['shortage']} ea",
                "실생산량": f"{item['actual_qty']} ea",
                "완료 예정": item["estimated_completion"],
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

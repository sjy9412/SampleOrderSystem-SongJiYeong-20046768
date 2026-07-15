from __future__ import annotations
from models.base import ModelEvent
from views.display import (
    console, print_table, show_menu_panel,
    prompt_choice, prompt_input, section,
    error, info, warn,
    STATUS_STYLES,
)
from rich.table import Table
from rich import box
from rich.text import Text


class MonitoringView:

    def __init__(self) -> None:
        pass

    def show_menu(self) -> None:
        console.print()
        show_menu_panel("모니터링", [
            ("1", "주문량 확인 (상태별)"),
            ("2", "재고량 확인 (시료별)"),
            ("0", "뒤로"),
        ])

    def get_menu_choice(self) -> str:
        return prompt_choice()

    def show_order_counts(self, counts: dict) -> None:
        section("주문량 현황 (상태별)")
        t = Table(box=box.ROUNDED, show_lines=False,
                  header_style="bold white", border_style="bright_black", expand=False)
        t.add_column("상태", min_width=12)
        t.add_column("건수", justify="right", min_width=6)
        statuses = ("RESERVED", "PRODUCING", "CONFIRMED", "RELEASE")
        for status in statuses:
            style = STATUS_STYLES.get(status, "")
            t.add_row(
                Text(status, style=style),
                Text(f"{counts.get(status, 0)}건", style=style),
            )
        console.print(t)

    def show_inventory_status(self, items: list[dict]) -> None:
        section("재고 현황 (시료별)")
        if not items:
            info("등록된 재고가 없습니다.")
            return
        rows = [
            {
                "시료명": item["name"],
                "재고 수량": str(item["quantity"]),
                "status": item["status"],
            }
            for item in items
        ]
        print_table(rows, col_labels={"status": "상태"})

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

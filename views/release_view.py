from __future__ import annotations
from models.base import ModelEvent
from views.display import (
    console, print_table, show_menu_panel,
    prompt_choice, prompt_input, section,
    error, info, warn,
)


class ReleaseView:

    def __init__(self, model) -> None:
        model.subscribe(self)

    def show_menu(self) -> None:
        console.print()
        show_menu_panel("출고 처리", [
            ("1", "출고 가능 주문 목록 (CONFIRMED)"),
            ("2", "출고 처리"),
            ("0", "뒤로"),
        ])

    def get_menu_choice(self) -> str:
        return prompt_choice()

    def get_order_id(self, action: str) -> str:
        return prompt_input(f"{action}할 주문 ID:")

    def show_orders(self, orders: list[dict]) -> None:
        section("출고 가능 주문 목록")
        if not orders:
            info("출고 가능한 주문이 없습니다.")
            return
        rows = [
            {
                "ID": o["id"],
                "고객명": o["customer_name"],
                "수량": str(o["quantity"]),
                "status": o["status"],
            }
            for o in orders
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

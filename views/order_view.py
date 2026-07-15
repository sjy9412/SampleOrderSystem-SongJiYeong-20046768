from __future__ import annotations
from models.base import ModelEvent
from views.display import (
    console, print_table, show_menu_panel,
    prompt_choice, prompt_input, section,
    success, error, info, warn,
)


class OrderView:

    def __init__(self, model) -> None:
        model.subscribe(self)

    def show_menu(self) -> None:
        console.print()
        show_menu_panel("주문 관리", [
            ("1", "주문 접수 (예약)"),
            ("2", "주문 승인 / 거절"),
            ("0", "뒤로"),
        ])

    def show_reserve_menu(self) -> None:
        console.print()
        show_menu_panel("시료 주문", [
            ("1", "주문 접수 (예약)"),
            ("0", "뒤로"),
        ])

    def show_approve_reject_menu(self) -> None:
        console.print()
        show_menu_panel("주문 승인 / 거절", [
            ("1", "주문 처리"),
            ("0", "뒤로"),
        ])

    def get_menu_choice(self) -> str:
        return prompt_choice()

    def get_order_input(self) -> tuple[str, str, int]:
        section("주문 접수")
        sample_id = prompt_input("시료 ID:")
        customer_name = prompt_input("고객명:")
        quantity = int(prompt_input("수량(ea):"))
        return sample_id, customer_name, quantity

    def get_order_id(self, action: str) -> str:
        return prompt_input(f"{action}할 주문 ID:")

    def get_approve_or_reject(self) -> str:
        show_menu_panel("승인 / 거절", [("1", "승인"), ("2", "거절")])
        choice = prompt_choice()
        return "승인" if choice == "1" else "거절"

    def show_orders(self, orders: list[dict]) -> None:
        section("주문 목록")
        if not orders:
            info("주문이 없습니다.")
            return
        rows = [
            {
                "ID": o["id"],
                "고객명": o["customer_name"],
                "수량": f"{o['quantity']} ea",
                "status": o["status"],
            }
            for o in orders
        ]
        print_table(rows, col_labels={"status": "상태"})

    def show_stock_insufficient(self, stock: int, required: int) -> None:
        warn(f"재고 부족 — 현재 재고: [bold]{stock}[/bold], 주문 수량: [bold]{required}[/bold]")
        info("생산 라인에 등록하면 [bold cyan]PRODUCING[/bold cyan] 상태로 전환됩니다.")

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

    def show_order_confirmation(self, sample_id: str, customer_name: str, quantity: int) -> None:
        from rich.panel import Panel
        from views.display import console
        body = (
            f"  시료 ID:  [bold]{sample_id}[/bold]\n"
            f"  고객명:   [bold]{customer_name}[/bold]\n"
            f"  수량:     [bold]{quantity} ea[/bold]"
        )
        console.print(Panel(
            body,
            title="[bold cyan]주문 확인[/bold cyan]",
            border_style="bright_black",
            expand=False,
            padding=(0, 1),
        ))

    def get_confirm_yn(self) -> str:
        console.print("\n  [bold yellow]예약 접수 하시겠습니까? (Y/N)[/bold yellow] ", end="")
        return input().strip()

    def show_reserve_success(self, order_no: str, status: str) -> None:
        from views.display import _STATUS_STYLES
        style = _STATUS_STYLES.get(status, "")
        success("예약 접수 완료")
        console.print(f"  주문번호: [bold cyan]{order_no}[/bold cyan]")
        console.print(f"  현재 상태: [{style}]{status}[/{style}]")

    def show_reserve_cancelled(self) -> None:
        info("예약 접수가 취소되었습니다.")

    def on_model_changed(self, event: ModelEvent) -> None:
        pass

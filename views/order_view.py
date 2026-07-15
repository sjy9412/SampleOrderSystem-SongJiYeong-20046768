from __future__ import annotations
from models.base import ModelEvent


class OrderView:

    MENU = (
        "\n[주문 관리]\n"
        "1. 주문 접수 (예약)\n"
        "2. 주문 승인/거절\n"
        "0. 뒤로\n"
    )

    def __init__(self, model) -> None:
        model.subscribe(self)

    def show_menu(self) -> None:
        print(self.MENU)

    def get_menu_choice(self) -> str:
        return input("선택: ").strip()

    def get_order_input(self) -> tuple[str, str, int]:
        sample_id = input("시료 ID: ").strip()
        customer_name = input("고객명: ").strip()
        quantity = int(input("수량: ").strip())
        return sample_id, customer_name, quantity

    def get_order_id(self, action: str) -> str:
        return input(f"{action}할 주문 ID: ").strip()

    def get_approve_or_reject(self) -> str:
        print("1. 승인  2. 거절")
        choice = input("선택: ").strip()
        return "승인" if choice == "1" else "거절"

    def show_orders(self, orders: list[dict]) -> None:
        if not orders:
            print("주문이 없습니다.")
            return
        header = f"{'ID':<38} {'고객명':<12} {'수량':>6} {'상태':<10}"
        print(header)
        print("-" * len(header))
        for o in orders:
            print(
                f"{o['id']:<38} "
                f"{o['customer_name']:<12} "
                f"{o['quantity']:>6} "
                f"{o['status']:<10}"
            )

    def show_stock_insufficient(self, stock: int, required: int) -> None:
        print(f"[재고 부족] 현재 재고: {stock}, 주문 수량: {required}")
        print("생산 라인에 등록하면 PRODUCING 상태로 전환됩니다.")

    def show_error(self, message: str) -> None:
        print(f"[오류] {message}")

    def show_invalid_input(self) -> None:
        print("잘못된 입력입니다.")

    def show_exit(self) -> None:
        print("뒤로 갑니다.")

    def get_title_input(self) -> str:
        return input("제목: ").strip()

    def get_id_input(self, action: str) -> str:
        return input(f"{action} ID: ").strip()

    def on_model_changed(self, event: ModelEvent) -> None:
        pass

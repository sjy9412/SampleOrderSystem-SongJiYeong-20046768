from __future__ import annotations
from models.base import ModelEvent


class ReleaseView:

    MENU = (
        "\n[출고 처리]\n"
        "1. 출고 가능 주문 목록 (CONFIRMED)\n"
        "2. 출고 처리\n"
        "0. 뒤로\n"
    )

    def __init__(self, model) -> None:
        model.subscribe(self)

    def show_menu(self) -> None:
        print(self.MENU)

    def get_menu_choice(self) -> str:
        return input("선택: ").strip()

    def get_order_id(self, action: str) -> str:
        return input(f"{action}할 주문 ID: ").strip()

    def show_orders(self, orders: list[dict]) -> None:
        if not orders:
            print("출고 가능한 주문이 없습니다.")
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

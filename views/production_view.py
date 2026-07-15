from __future__ import annotations
from models.base import ModelEvent


class ProductionView:

    MENU = (
        "\n[생산 라인]\n"
        "1. 생산 현황 조회\n"
        "2. 대기 주문 목록\n"
        "0. 뒤로\n"
    )

    def __init__(self, model) -> None:
        model.subscribe(self)

    def show_menu(self) -> None:
        print(self.MENU)

    def get_menu_choice(self) -> str:
        return input("선택: ").strip()

    def show_current(self, info: dict) -> None:
        print("\n[현재 생산 현황]")
        header = f"{'주문 ID':<38} {'시료명':<12} {'주문 수량':>8} {'실 생산량':>8} {'총 생산시간(h)':>14}"
        print(header)
        print("-" * len(header))
        print(
            f"{info['order_id']:<38} "
            f"{info['sample_name']:<12} "
            f"{info['quantity']:>8} "
            f"{info['actual_qty']:>8} "
            f"{info['total_time']:>14.1f}"
        )

    def show_no_current(self) -> None:
        print("현재 생산 중인 주문이 없습니다.")

    def show_queue(self, items: list[dict]) -> None:
        print("\n[대기 주문 목록]")
        if not items:
            print("대기 중인 주문이 없습니다.")
            return
        header = f"{'순번':>4} {'주문 ID':<38} {'시료명':<12} {'고객명':<12} {'수량':>6}"
        print(header)
        print("-" * len(header))
        for item in items:
            print(
                f"{item['position']:>4} "
                f"{item['order_id']:<38} "
                f"{item['sample_name']:<12} "
                f"{item['customer_name']:<12} "
                f"{item['quantity']:>6}"
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

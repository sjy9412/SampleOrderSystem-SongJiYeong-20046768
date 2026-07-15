from __future__ import annotations
from models.base import ModelEvent


class MonitoringView:

    MENU = (
        "\n[모니터링]\n"
        "1. 주문량 확인 (상태별)\n"
        "2. 재고량 확인 (시료별)\n"
        "0. 뒤로\n"
    )

    def __init__(self) -> None:
        pass

    def show_menu(self) -> None:
        print(self.MENU)

    def get_menu_choice(self) -> str:
        return input("선택: ").strip()

    def show_order_counts(self, counts: dict) -> None:
        print("\n[주문량 현황 (상태별)]")
        header = f"{'상태':<12} {'건수':>6}"
        print(header)
        print("-" * len(header))
        for status in ("RESERVED", "PRODUCING", "CONFIRMED", "RELEASE"):
            print(f"{status:<12} {counts.get(status, 0):>6}건")

    def show_inventory_status(self, items: list[dict]) -> None:
        print("\n[재고 현황 (시료별)]")
        if not items:
            print("등록된 재고가 없습니다.")
            return
        header = f"{'시료명':<16} {'재고 수량':>10} {'상태':<6}"
        print(header)
        print("-" * len(header))
        for item in items:
            print(f"{item['name']:<16} {item['quantity']:>10} {item['status']:<6}")

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

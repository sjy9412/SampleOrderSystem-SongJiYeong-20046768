from __future__ import annotations
from datetime import datetime, timezone
from models.base import ModelEvent
from views.display import (
    console, print_table, section,
    prompt_input, success, info, error, warn,
)


class ReleaseView:

    def __init__(self, model) -> None:
        model.subscribe(self)

    def show_confirmed_orders(self, orders: list[dict]) -> None:
        section("출고 가능 주문 목록")
        if not orders:
            info("출고 가능한 주문이 없습니다.")
            return
        rows = [
            {
                "번호": str(i + 1),
                "주문번호": o["order_no"],
                "고객": o["customer_name"],
                "시료": o["sample_id"],
                "수량": f"{o['quantity']} ea",
            }
            for i, o in enumerate(orders)
        ]
        print_table(rows)

    def get_release_number(self, count: int) -> str:
        return prompt_input(f"출고할 번호를 입력하세요 (1-{count}):")

    def show_release_result(self, order: dict) -> None:
        success("출고처리 완료.")
        timestamp = _format_timestamp(order.get("updated_at", ""))
        rows = [
            {"항목": "주문 번호", "내용": order.get("order_no", "")},
            {"항목": "출고 수량", "내용": f"{order.get('quantity', '')} ea"},
            {"항목": "처리 일시", "내용": timestamp},
            {"항목": "상태", "내용": order.get("status", "")},
        ]
        print_table(rows)

    def show_error(self, message: str) -> None:
        error(message)

    def show_invalid_input(self) -> None:
        warn("잘못된 입력입니다.")

    def on_model_changed(self, event: ModelEvent) -> None:
        pass


def _format_timestamp(iso: str) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return iso

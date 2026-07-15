from __future__ import annotations


class ReleaseController:

    def __init__(self, order_model, view) -> None:
        self._order = order_model
        self._view = view

    def run(self) -> None:
        orders = self._order.get_by_status("CONFIRMED")
        self._view.show_confirmed_orders(orders)
        if not orders:
            return
        choice = self._view.get_release_number(len(orders))
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(orders):
                self._view.show_error("유효하지 않은 번호입니다.")
                return
            released = self._order.release(orders[idx]["id"])
            self._view.show_release_result(released)
        except (ValueError, KeyError) as e:
            self._view.show_error(str(e))

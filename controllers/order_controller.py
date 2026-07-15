from __future__ import annotations


class ReserveController:

    def __init__(self, order_model, view) -> None:
        self._order = order_model
        self._view = view

    def run(self) -> None:
        self._handle_reserve()

    def _handle_reserve(self) -> None:
        sample_id, customer_name, quantity = self._view.get_order_input()
        self._view.show_order_confirmation(sample_id, customer_name, quantity)
        yn = self._view.get_confirm_yn()
        if yn.upper() == "Y":
            order = self._order.reserve(sample_id, customer_name, quantity)
            self._view.show_reserve_success(order["order_no"], order["status"])
        else:
            self._view.show_reserve_cancelled()

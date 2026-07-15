from __future__ import annotations


class ReserveController:

    def __init__(self, order_model, view) -> None:
        self._order = order_model
        self._view = view

    def run(self) -> None:
        while True:
            self._view.show_reserve_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                break
            elif choice == "1":
                self._handle_reserve()
            else:
                self._view.show_invalid_input()

    def _handle_reserve(self) -> None:
        sample_id, customer_name, quantity = self._view.get_order_input()
        self._order.reserve(sample_id, customer_name, quantity)

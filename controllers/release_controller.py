from __future__ import annotations


class ReleaseController:

    def __init__(self, order_model, view) -> None:
        self._order = order_model
        self._view = view

    def run(self) -> None:
        while True:
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                break
            elif choice == "1":
                self._handle_list_confirmed()
            elif choice == "2":
                self._handle_release()
            else:
                self._view.show_invalid_input()

    def _handle_list_confirmed(self) -> None:
        orders = self._order.get_by_status("CONFIRMED")
        self._view.show_orders(orders)

    def _handle_release(self) -> None:
        order_id = self._view.get_order_id("출고")
        if not order_id:
            return
        try:
            self._order.release(order_id)
        except (ValueError, KeyError) as e:
            self._view.show_error(str(e))

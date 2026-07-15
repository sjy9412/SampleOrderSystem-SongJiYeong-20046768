from __future__ import annotations


class ApproveRejectController:

    def __init__(self, order_model, inventory_model, production_line, view) -> None:
        self._order = order_model
        self._inventory = inventory_model
        self._production_line = production_line
        self._view = view

    def run(self) -> None:
        while True:
            self._view.show_approve_reject_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                break
            elif choice == "1":
                self._handle_approve_reject()
            else:
                self._view.show_invalid_input()

    def _handle_approve_reject(self) -> None:
        self._view.show_orders(self._order.get_reserved())

        order_id = self._view.get_order_id("처리")
        if not order_id:
            return

        order = self._order.get_by_id(order_id)
        if order is None:
            self._view.show_error(f"주문을 찾을 수 없습니다: {order_id}")
            return

        if self._view.get_approve_or_reject() == "거절":
            self._order.reject(order_id)
        else:
            self._approve(order)

    def _approve(self, order: dict) -> None:
        order_id = order["id"]
        sample_id, quantity = order["sample_id"], order["quantity"]

        if self._inventory.is_sufficient(sample_id, quantity):
            self._inventory.decrease(sample_id, quantity)
            self._order.confirm(order_id)
        else:
            self._view.show_stock_insufficient(self._inventory.get_stock(sample_id), quantity)
            if self._view.get_approve_or_reject() == "승인":
                self._order.set_producing(order_id)
                self._production_line.enqueue(order_id)
            else:
                self._order.reject(order_id)

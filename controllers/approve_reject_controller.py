from __future__ import annotations
from views.display import separator


class ApproveRejectController:

    def __init__(self, order_model, sample_model, inventory_model, production_line, view) -> None:
        self._order = order_model
        self._sample = sample_model
        self._inventory = inventory_model
        self._production_line = production_line
        self._view = view

    def run(self) -> None:
        while True:
            reserved = self._order.get_reserved()
            self._view.show_reserved_orders_numbered(reserved)
            if not reserved:
                break
            choice = self._view.get_order_number_choice(len(reserved))
            if choice == 0:
                break
            if not (1 <= choice <= len(reserved)):
                self._view.show_invalid_input()
                continue
            separator()
            self._process_order(reserved[choice - 1])
            separator()

    def _process_order(self, order: dict) -> None:
        order_id = order["id"]
        sample_id = order["sample_id"]
        quantity = order["quantity"]

        sample = self._sample.get_by_id(sample_id)
        sample_name = sample["name"] if sample else sample_id
        stock = self._inventory.get_stock(sample_id)
        shortage = max(0, quantity - stock)

        self._view.show_stock_checking(sample_name)
        self._view.show_stock_detail(sample_name, stock, quantity, shortage)

        if shortage == 0:
            self._inventory.decrease(sample_id, quantity)
            updated = self._order.confirm(order_id)
            self._view.show_approve_result(updated["order_no"], updated["status"])
        else:
            if self._view.get_approve_or_reject() == "승인":
                self._order.set_producing(order_id)
                self._production_line.enqueue(order_id)
                updated = self._order.get_by_id(order_id)
                self._view.show_approve_result(updated["order_no"], updated["status"])
            else:
                updated = self._order.reject(order_id)
                self._view.show_approve_result(updated["order_no"], updated["status"])

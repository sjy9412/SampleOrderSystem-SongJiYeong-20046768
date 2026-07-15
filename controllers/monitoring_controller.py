from __future__ import annotations
from views.display import separator


class MonitoringController:

    def __init__(self, order_model, inventory_model, sample_model, view) -> None:
        self._order = order_model
        self._inventory = inventory_model
        self._sample = sample_model
        self._view = view

    def run(self) -> None:
        first = True
        while True:
            if not first:
                separator()
            first = False
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                break
            elif choice == "1":
                separator()
                self._handle_order_counts()
            elif choice == "2":
                separator()
                self._handle_inventory_status()
            else:
                self._view.show_invalid_input()

    def _handle_order_counts(self) -> None:
        counts = {
            status: len(self._order.get_by_status(status))
            for status in ("RESERVED", "PRODUCING", "CONFIRMED", "RELEASE")
        }
        self._view.show_order_counts(counts)

    def _handle_inventory_status(self) -> None:
        stocks = self._inventory.get_all_stocks()
        reserved = self._order.get_by_status("RESERVED")
        producing = self._order.get_by_status("PRODUCING")
        pending_all = reserved + producing

        items = []
        for stock in stocks:
            sample_id = stock["sample_id"]
            sample = self._sample.get_by_id(sample_id)
            name = sample["name"] if sample else "알 수 없음"
            pending_qty = sum(
                o["quantity"] for o in pending_all if o["sample_id"] == sample_id
            )
            status = self._inventory.get_status(sample_id, pending_qty)
            items.append({
                "name": name,
                "quantity": stock["quantity"],
                "status": status,
            })
        self._view.show_inventory_status(items)

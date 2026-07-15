from __future__ import annotations
import math
from db import json_store as store
from models.base import ObservableModel

COLLECTION = "production_queue"


class ProductionLine(ObservableModel):

    def __init__(self, order_model, inventory_model, sample_model) -> None:
        super().__init__()
        self._order_model = order_model
        self._inventory_model = inventory_model
        self._sample_model = sample_model

    def enqueue(self, order_id: str) -> dict:
        return store.create(COLLECTION, {"order_id": order_id})

    def get_queue(self) -> list[dict]:
        items = store.read_all(COLLECTION)
        return sorted(items, key=lambda x: x["created_at"])

    def get_current(self) -> dict | None:
        queue = self.get_queue()
        return queue[0] if queue else None

    def calculate_production(
        self, shortage: int, yield_rate: float, avg_time: float
    ) -> tuple[int, float]:
        actual_qty = math.ceil(shortage / yield_rate)
        total_time = avg_time * actual_qty
        return actual_qty, total_time

    def get_current_info(self) -> dict | None:
        current = self.get_current()
        if current is None:
            return None
        order = self._order_model.get_by_id(current["order_id"])
        sample = self._sample_model.get_by_id(order["sample_id"])
        stock = self._inventory_model.get_stock(order["sample_id"])
        shortage = max(0, order["quantity"] - stock)
        actual_qty, total_time = self.calculate_production(
            shortage, sample["yield_rate"], sample["avg_production_time"]
        )
        return {
            "order_id": order["id"],
            "sample_name": sample["name"],
            "quantity": order["quantity"],
            "actual_qty": actual_qty,
            "total_time": total_time,
        }

    def get_queue_info(self) -> list[dict]:
        result = []
        for i, item in enumerate(self.get_queue(), 1):
            order = self._order_model.get_by_id(item["order_id"])
            sample = self._sample_model.get_by_id(order["sample_id"])
            result.append({
                "position": i,
                "order_id": order["id"],
                "sample_name": sample["name"],
                "customer_name": order["customer_name"],
                "quantity": order["quantity"],
            })
        return result

    def complete(self, order_id: str) -> None:
        order = self._order_model.get_by_id(order_id)
        sample = self._sample_model.get_by_id(order["sample_id"])
        current_stock = self._inventory_model.get_stock(order["sample_id"])
        shortage = order["quantity"] - current_stock
        actual_qty, _ = self.calculate_production(
            shortage, sample["yield_rate"], sample["avg_production_time"]
        )
        self._inventory_model.increase(order["sample_id"], actual_qty)
        self._order_model.confirm_production(order_id)
        for item in store.read_all(COLLECTION, order_id=order_id):
            store.delete(COLLECTION, item["id"])

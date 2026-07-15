from __future__ import annotations
from datetime import date
from models.base import ObservableModel, ModelEvent, EventType
from db import json_store as store


class OrderModel(ObservableModel):
    COLLECTION = "orders"

    def _generate_order_no(self) -> str:
        today = date.today().strftime("%Y%m%d")
        prefix = f"ORD-{today}-"
        existing = [
            o["order_no"] for o in store.read_all(self.COLLECTION)
            if o.get("order_no", "").startswith(prefix)
        ]
        seq = max((int(n.split("-")[2]) for n in existing), default=0) + 1
        return f"{prefix}{seq:04d}"

    def reserve(self, sample_id: str, customer_name: str, quantity: int) -> dict:
        record = store.create(self.COLLECTION, {
            "order_no": self._generate_order_no(),
            "sample_id": sample_id,
            "customer_name": customer_name,
            "quantity": quantity,
            "status": "RESERVED",
        })
        self._notify(ModelEvent(EventType.ADDED, record))
        return record

    def get_all(self) -> list[dict]:
        return store.read_all(self.COLLECTION)

    def get_reserved(self) -> list[dict]:
        return store.read_all(self.COLLECTION, status="RESERVED")

    def get_by_status(self, status: str) -> list[dict]:
        return store.read_all(self.COLLECTION, status=status)

    def get_by_id(self, order_id: str) -> dict | None:
        return store.read_one(self.COLLECTION, order_id)

    def _transition(self, order_id: str, from_status: str, to_status: str) -> dict:
        order = store.read_one(self.COLLECTION, order_id)
        if order is None or order["status"] != from_status:
            raise ValueError(f"주문 {order_id}의 상태가 {from_status}가 아닙니다.")
        return store.update(self.COLLECTION, order_id, {"status": to_status})

    def confirm(self, order_id: str) -> dict:
        return self._transition(order_id, "RESERVED", "CONFIRMED")

    def reject(self, order_id: str) -> dict:
        return self._transition(order_id, "RESERVED", "REJECTED")

    def set_producing(self, order_id: str) -> dict:
        return self._transition(order_id, "RESERVED", "PRODUCING")

    def confirm_production(self, order_id: str) -> dict:
        return self._transition(order_id, "PRODUCING", "CONFIRMED")

    def release(self, order_id: str) -> dict:
        return self._transition(order_id, "CONFIRMED", "RELEASE")

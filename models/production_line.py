from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta
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

    def auto_complete_if_done(self, now: datetime | None = None) -> bool:
        current = self.get_current()
        if current is None:
            return False
        if now is None:
            now = datetime.now(timezone.utc)
        order = self._order_model.get_by_id(current["order_id"])
        sample = self._sample_model.get_by_id(order["sample_id"])
        stock = self._inventory_model.get_stock(order["sample_id"])
        shortage = max(0, order["quantity"] - stock)
        _, total_time = self.calculate_production(
            shortage, sample["yield_rate"], sample["avg_production_time"]
        )
        started_at = datetime.fromisoformat(current["created_at"])
        elapsed_min = (now - started_at).total_seconds() / 60
        if total_time == 0 or elapsed_min >= total_time:
            self.complete(current["order_id"])
            self.auto_complete_if_done(now=now)
            return True
        return False

    def get_current_info(self, now: datetime | None = None) -> dict | None:
        if now is None:
            now = datetime.now(timezone.utc)
        self.auto_complete_if_done(now=now)
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
        started_at = datetime.fromisoformat(current["created_at"])
        elapsed_min = (now - started_at).total_seconds() / 60
        progress_pct = min(100.0, elapsed_min / total_time * 100) if total_time > 0 else 100.0
        completion_dt = started_at + timedelta(minutes=total_time)
        estimated_completion = completion_dt.astimezone().strftime("%Y-%m-%d %H:%M")
        return {
            "order_id": order["id"],
            "order_no": order["order_no"],
            "sample_name": sample["name"],
            "quantity": order["quantity"],
            "stock": stock,
            "shortage": shortage,
            "yield_rate": sample["yield_rate"],
            "avg_time": sample["avg_production_time"],
            "actual_qty": actual_qty,
            "total_time": total_time,
            "progress_pct": progress_pct,
            "estimated_completion": estimated_completion,
        }

    def get_queue_info(self, now: datetime | None = None) -> list[dict]:
        if now is None:
            now = datetime.now(timezone.utc)
        result = []
        queue = self.get_queue()
        waiting_queue = queue[1:]  # 첫 번째(현재 생산 중)는 제외
        if not waiting_queue:
            return result

        # 대기 항목의 시작 기준 = 현재 생산 중인 항목의 완료 시각
        current = queue[0]
        current_order = self._order_model.get_by_id(current["order_id"])
        current_sample = self._sample_model.get_by_id(current_order["sample_id"])
        current_stock = self._inventory_model.get_stock(current_order["sample_id"])
        current_shortage = max(0, current_order["quantity"] - current_stock)
        _, current_total_time = self.calculate_production(
            current_shortage, current_sample["yield_rate"], current_sample["avg_production_time"]
        )
        current_started_at = datetime.fromisoformat(current["created_at"])
        prev_completion = current_started_at + timedelta(minutes=current_total_time)

        for i, item in enumerate(waiting_queue, 1):
            order = self._order_model.get_by_id(item["order_id"])
            sample = self._sample_model.get_by_id(order["sample_id"])
            stock = self._inventory_model.get_stock(order["sample_id"])
            shortage = max(0, order["quantity"] - stock)
            actual_qty, total_time = self.calculate_production(
                shortage, sample["yield_rate"], sample["avg_production_time"]
            )
            completion_dt = prev_completion + timedelta(minutes=total_time)
            prev_completion = completion_dt
            estimated_completion = completion_dt.astimezone().strftime("%Y-%m-%d %H:%M")
            result.append({
                "position": i,
                "order_no": order["order_no"],
                "sample_name": sample["name"],
                "customer_name": order["customer_name"],
                "quantity": order["quantity"],
                "shortage": shortage,
                "actual_qty": actual_qty,
                "estimated_completion": estimated_completion,
            })
        return result

    def complete(self, order_id: str) -> None:
        order = self._order_model.get_by_id(order_id)
        sample = self._sample_model.get_by_id(order["sample_id"])
        current_stock = self._inventory_model.get_stock(order["sample_id"])
        shortage = max(0, order["quantity"] - current_stock)
        actual_qty, _ = self.calculate_production(
            shortage, sample["yield_rate"], sample["avg_production_time"]
        )
        self._inventory_model.increase(order["sample_id"], actual_qty)
        self._inventory_model.decrease(order["sample_id"], order["quantity"])
        self._order_model.confirm_production(order_id)
        for item in store.read_all(COLLECTION, order_id=order_id):
            store.delete(COLLECTION, item["id"])

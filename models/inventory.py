from db import json_store as store
from models.base import ObservableModel

COLLECTION = "inventories"


class InventoryModel(ObservableModel):

    def get_stock(self, sample_id: str) -> int:
        records = store.read_all(COLLECTION, sample_id=sample_id)
        return records[0]["quantity"] if records else 0

    def get_all_stocks(self) -> list[dict]:
        return store.read_all(COLLECTION)

    def is_sufficient(self, sample_id: str, quantity: int) -> bool:
        return self.get_stock(sample_id) >= quantity

    def increase(self, sample_id: str, quantity: int) -> None:
        records = store.read_all(COLLECTION, sample_id=sample_id)
        if records:
            record = records[0]
            store.update(COLLECTION, record["id"], {"quantity": record["quantity"] + quantity})
        else:
            store.create(COLLECTION, {"sample_id": sample_id, "quantity": quantity})

    def decrease(self, sample_id: str, quantity: int) -> None:
        current = self.get_stock(sample_id)
        if current < quantity:
            raise ValueError(f"재고 부족: 현재 {current}, 요청 {quantity}")
        records = store.read_all(COLLECTION, sample_id=sample_id)
        store.update(COLLECTION, records[0]["id"], {"quantity": current - quantity})

    def get_status(self, sample_id: str, ordered_quantity: int) -> str:
        stock = self.get_stock(sample_id)
        if stock == 0:
            return "고갈"
        if stock < ordered_quantity:
            return "부족"
        return "여유"

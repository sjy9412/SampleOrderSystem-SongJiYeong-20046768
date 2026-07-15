from __future__ import annotations
from models.base import ObservableModel, ModelEvent, EventType
from db import json_store as store

COLLECTION = "samples"


class SampleModel(ObservableModel):

    def add(self, name: str, avg_production_time: float, yield_rate: float) -> dict:
        existing = store.read_all(COLLECTION)
        for s in existing:
            if s["name"] == name:
                raise ValueError("이미 등록된 시료입니다.")
        next_id = f"S-{len(existing) + 1:03d}"
        record = store.create(COLLECTION, {
            "id": next_id,
            "name": name,
            "avg_production_time": avg_production_time,
            "yield_rate": yield_rate,
        })
        self._notify(ModelEvent(type=EventType.ADDED, payload=record))
        return record

    def get_all(self) -> list[dict]:
        return store.read_all(COLLECTION)

    def get_by_id(self, sample_id: str) -> dict | None:
        return store.read_one(COLLECTION, sample_id)

    def search(self, keyword: str) -> list[dict]:
        keyword_lower = keyword.lower()
        return [s for s in store.read_all(COLLECTION)
                if keyword_lower in s["name"].lower()]

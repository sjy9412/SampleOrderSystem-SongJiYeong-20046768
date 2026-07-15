"""db.json 을 조회할 때마다 읽는 단순 스토어."""
from __future__ import annotations

import copy
import json
from pathlib import Path


class DataStore:
    META_KEY = "_meta"

    def __init__(self, path: str | Path):
        self._path = Path(path)

    def _load(self) -> dict:
        raw = self._path.read_text(encoding="utf-8")
        return json.loads(raw)

    def _collections(self, parsed: dict) -> dict[str, list[dict]]:
        return {k: v for k, v in parsed.items()
                if k != self.META_KEY and isinstance(v, list)}

    def collections(self) -> list[str]:
        return list(self._collections(self._load()).keys())

    def all(self, collection: str) -> list[dict] | None:
        data = self._collections(self._load())
        return copy.deepcopy(data.get(collection))

    def get_by_id(self, collection: str, record_id: str) -> dict | None:
        rows = self.all(collection)
        if rows is None:
            return None
        needle = record_id.lower()
        return next((r for r in rows if str(r.get("id", "")).lower() == needle), None)

    def filter(self, collection: str, field: str, value: str) -> list[dict] | None:
        rows = self.all(collection)
        if rows is None:
            return None
        return [r for r in rows if value.lower() in str(r.get(field, "")).lower()]

    def stats(self) -> list[dict]:
        data = self._collections(self._load())
        return [
            {"collection": col, "count": len(rows), "fields": len(rows[0]) if rows else 0}
            for col, rows in data.items()
        ]

    def file_meta(self) -> dict:
        return self._load().get(self.META_KEY, {})

    def db_path(self) -> Path:
        return self._path

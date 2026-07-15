"""
JSON 기반 데이터 영속성 레이어 - CRUD PoC
파일 단위로 저장·불러오기, 컬렉션별 CRUD, 자동 ID 채번
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "db.json")


# ── 저수준: 파일 I/O ──────────────────────────────────────────────────────────

_INITIAL_DB: dict = {
    "_meta": {
        "version": 1,
        "created_at": "",
        "last_modified": "",
    }
}


def _init_db() -> dict:
    """db.json이 없으면 초기 구조로 파일을 생성하고 반환."""
    db = {**_INITIAL_DB, "_meta": {**_INITIAL_DB["_meta"], "created_at": _now()}}
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    return db


def _load() -> dict:
    if not os.path.exists(DB_PATH):
        return _init_db()
    with open(DB_PATH, "r", encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return _init_db()
    return json.loads(content)


def _save(data: dict) -> None:
    data["_meta"]["last_modified"] = _now()
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── 고수준: CRUD ───────────────────────────────────────────────────────────────

def create(collection: str, record: dict) -> dict:
    """레코드를 컬렉션에 추가하고 저장된 항목을 반환."""
    db = _load()
    db.setdefault(collection, [])
    record = {
        "id": str(uuid.uuid4()),
        "created_at": _now(),
        "updated_at": _now(),
        **record,
    }
    db[collection].append(record)
    _save(db)
    return record


def read_all(collection: str, **filters) -> list[dict]:
    """컬렉션 전체 또는 필터 조건과 일치하는 항목 목록을 반환."""
    db = _load()
    items = db.get(collection, [])
    if not filters:
        return items
    return [
        item for item in items
        if all(item.get(k) == v for k, v in filters.items())
    ]


def read_one(collection: str, record_id: str) -> Optional[dict]:
    """ID로 단일 레코드를 반환. 없으면 None."""
    for item in read_all(collection):
        if item.get("id") == record_id:
            return item
    return None


def update(collection: str, record_id: str, changes: dict) -> Optional[dict]:
    """ID와 일치하는 레코드를 부분 업데이트하고 갱신된 항목을 반환."""
    db = _load()
    for item in db.get(collection, []):
        if item["id"] == record_id:
            item.update({k: v for k, v in changes.items() if k not in ("id", "created_at")})
            item["updated_at"] = _now()
            _save(db)
            return item
    return None


def delete(collection: str, record_id: str) -> bool:
    """ID와 일치하는 레코드를 삭제. 성공 여부를 반환."""
    db = _load()
    original = db.get(collection, [])
    filtered = [item for item in original if item["id"] != record_id]
    if len(filtered) == len(original):
        return False
    db[collection] = filtered
    _save(db)
    return True


def reset(collection: str) -> None:
    """컬렉션의 모든 레코드를 삭제."""
    db = _load()
    db[collection] = []
    _save(db)

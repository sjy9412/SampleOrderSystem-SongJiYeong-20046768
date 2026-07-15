"""
Dummy Data Generator PoC
- 스키마 정의만으로 임의 데이터를 생성해 json_store에 삽입
- 지원 필드 타입: name, email, phone, address, company, date, int, float, bool, choice, text, uuid
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from faker import Faker
import json_store

fake = Faker("ko_KR")

# ── 필드 타입 → 생성 함수 매핑 ────────────────────────────────────────────────

_GENERATORS: dict[str, Any] = {
    "name":       lambda cfg: fake.name(),
    "email":      lambda cfg: fake.email(),
    "phone":      lambda cfg: fake.phone_number(),
    "address":    lambda cfg: fake.address().replace("\n", " "),
    "company":    lambda cfg: fake.company(),
    "date":       lambda cfg: fake.date_between(
                      start_date=cfg.get("start", "-5y"),
                      end_date=cfg.get("end", "today"),
                  ).isoformat(),
    "int":        lambda cfg: random.randint(cfg.get("min", 0), cfg.get("max", 100)),
    "float":      lambda cfg: round(
                      random.uniform(cfg.get("min", 0.0), cfg.get("max", 1.0)),
                      cfg.get("precision", 2),
                  ),
    "bool":       lambda cfg: random.choice([True, False]),
    "choice":     lambda cfg: random.choice(cfg["options"]),
    "text":       lambda cfg: fake.text(max_nb_chars=cfg.get("max_chars", 200)),
    "uuid":       lambda cfg: fake.uuid4(),
    "url":        lambda cfg: fake.url(),
    "username":   lambda cfg: fake.user_name(),
    "password":   lambda cfg: fake.password(length=cfg.get("length", 12)),
    "ip":         lambda cfg: fake.ipv4(),
    "color":      lambda cfg: fake.color_name(),
    "job":        lambda cfg: fake.job(),
    "sentence":   lambda cfg: fake.sentence(nb_words=cfg.get("nb_words", 8)),
}


def _generate_value(field_spec: dict) -> Any:
    field_type = field_spec.get("type", "text")
    generator = _GENERATORS.get(field_type)
    if generator is None:
        raise ValueError(f"알 수 없는 필드 타입: '{field_type}'. 지원 타입: {list(_GENERATORS)}")
    return generator(field_spec)


def generate_record(schema: dict[str, dict]) -> dict:
    """스키마 정의에 따라 레코드 1건을 생성한다."""
    return {field_name: _generate_value(spec) for field_name, spec in schema.items()}


def bulk_insert(collection: str, schema: dict[str, dict], count: int = 10) -> list[dict]:
    """schema 기반으로 count개의 레코드를 생성해 collection에 삽입하고 결과를 반환."""
    inserted = []
    for _ in range(count):
        record = generate_record(schema)
        saved = json_store.create(collection, record)
        inserted.append(saved)
    print(f"[✓] '{collection}' 컬렉션에 {len(inserted)}건 삽입 완료")
    return inserted


# ── 내장 샘플 스키마 ──────────────────────────────────────────────────────────

SCHEMAS: dict[str, dict] = {
    "users": {
        "name":       {"type": "name"},
        "email":      {"type": "email"},
        "phone":      {"type": "phone"},
        "username":   {"type": "username"},
        "password":   {"type": "password", "length": 16},
        "is_active":  {"type": "bool"},
        "role":       {"type": "choice", "options": ["admin", "editor", "viewer"]},
        "joined_at":  {"type": "date", "start": "-3y", "end": "today"},
    },
    "products": {
        "name":        {"type": "sentence", "nb_words": 4},
        "description": {"type": "text", "max_chars": 300},
        "price":       {"type": "float", "min": 100.0, "max": 500000.0, "precision": 0},
        "stock":       {"type": "int", "min": 0, "max": 999},
        "category":    {"type": "choice", "options": ["전자기기", "의류", "식품", "스포츠", "도서"]},
        "is_available":{"type": "bool"},
        "created_at":  {"type": "date", "start": "-2y", "end": "today"},
    },
    "orders": {
        "order_number":   {"type": "uuid"},
        "customer_name":  {"type": "name"},
        "customer_email": {"type": "email"},
        "total_amount":   {"type": "float", "min": 1000.0, "max": 1000000.0, "precision": 0},
        "status":         {"type": "choice", "options": ["pending", "paid", "shipped", "delivered", "cancelled"]},
        "ordered_at":     {"type": "date", "start": "-1y", "end": "today"},
        "address":        {"type": "address"},
    },
}

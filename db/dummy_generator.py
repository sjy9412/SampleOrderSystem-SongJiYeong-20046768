"""
Dummy Data Generator PoC
- 스키마 정의만으로 임의 데이터를 생성해 json_store에 삽입
- 지원 필드 타입: name, email, phone, address, company, date, int, float, bool, choice, text, uuid

도메인 데이터 생성:
  generate_domain_data(sample_count=5, order_count=10)
"""

from __future__ import annotations

import random
from datetime import date
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


# ── 도메인 데이터 생성 ────────────────────────────────────────────────────────

_SAMPLE_NAMES = [
    "실리콘 웨이퍼-8인치",
    "실리콘 웨이퍼-12인치",
    "GaAs 기판-4인치",
    "SiC 웨이퍼-4인치",
    "InP 기판-3인치",
    "게르마늄 웨이퍼-6인치",
    "사파이어 기판-4인치",
    "GaN-on-Si 웨이퍼",
]

_CUSTOMER_NAMES = [
    "삼성전자", "SK하이닉스", "LG이노텍", "DB하이텍", "키파운드리",
    "매그나칩반도체", "하나마이크론", "SFA반도체", "네패스", "시그네틱스",
]

# 상태 분포: RESERVED 비중을 높게 설정 (승인 대기 중인 주문이 많은 현실 반영)
_NON_PRODUCING_STATUSES = ["RESERVED", "RESERVED", "CONFIRMED", "RELEASE", "REJECTED"]


def generate_domain_data(
    sample_count: int = 5,
    order_count: int = 10,
    inventory_count: int = 3,
    queue_count: int = 3,
) -> dict:
    """
    실제 도메인 컬렉션에 맞는 더미 데이터를 순서대로 생성·삽입한다.

    삽입 순서: samples → orders → inventories → production_queue
    - inventory_count: 재고 레코드를 생성할 시료 수 (나머지 시료는 재고 없음)
    - queue_count: PRODUCING 상태로 강제할 주문 수 (= 생산 큐 크기)
    """
    # 1. samples
    names = random.sample(_SAMPLE_NAMES, min(sample_count, len(_SAMPLE_NAMES)))
    samples = []
    for name in names:
        existing_count = len(json_store.read_all("samples"))
        record = json_store.create("samples", {
            "id": f"S-{existing_count + 1:03d}",
            "name": name,
            "avg_production_time": round(random.uniform(0.5, 10.0), 1),
            "yield_rate": round(random.uniform(0.70, 0.99), 2),
        })
        samples.append(record)
    print(f"[✓] 'samples' {len(samples)}건 삽입")

    # 2. orders — 앞 queue_count개는 PRODUCING 고정, 나머지는 랜덤
    actual_queue = min(queue_count, order_count)
    today = date.today().strftime("%Y%m%d")
    prefix = f"ORD-{today}-"
    existing_nos = [
        o["order_no"] for o in json_store.read_all("orders")
        if o.get("order_no", "").startswith(prefix)
    ]
    seq_start = max((int(n.split("-")[2]) for n in existing_nos), default=0) + 1
    orders = []
    for i in range(order_count):
        status = "PRODUCING" if i < actual_queue else random.choice(_NON_PRODUCING_STATUSES)
        order_no = f"{prefix}{(seq_start + i):04d}"
        record = json_store.create("orders", {
            "order_no": order_no,
            "sample_id": random.choice(samples)["id"],
            "customer_name": random.choice(_CUSTOMER_NAMES),
            "quantity": random.randint(10, 500),
            "status": status,
        })
        orders.append(record)
    print(f"[✓] 'orders' {len(orders)}건 삽입")

    # 3. inventories — inventory_count개 시료에만 재고 레코드 생성 (나머지는 재고 없음)
    actual_inv = min(inventory_count, len(samples))
    for sample in random.sample(samples, actual_inv):
        json_store.create("inventories", {
            "sample_id": sample["id"],
            "quantity": random.randint(0, 300),
        })
    print(f"[✓] 'inventories' {actual_inv}건 삽입")

    # 4. production_queue — PRODUCING 주문 전체 등록
    producing = [o for o in orders if o["status"] == "PRODUCING"]
    for order in producing:
        json_store.create("production_queue", {"order_id": order["id"]})
    print(f"[✓] 'production_queue' {len(producing)}건 삽입")

    return {"samples": samples, "orders": orders}


# ── 내장 샘플 스키마 (범용) ───────────────────────────────────────────────────

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
}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="도메인 더미 데이터 생성기")
    parser.add_argument("--samples",     type=int, default=5,  metavar="N", help="시료 수 (기본 5)")
    parser.add_argument("--orders",      type=int, default=10, metavar="N", help="주문 수 (기본 10)")
    parser.add_argument("--inventories", type=int, default=3,  metavar="N", help="재고 레코드 수 (기본 3)")
    parser.add_argument("--queue",       type=int, default=3,  metavar="N", help="생산 큐 크기 (기본 3)")
    args = parser.parse_args()

    for col in ("samples", "orders", "inventories", "production_queue"):
        json_store.reset(col)
    print("기존 도메인 데이터 초기화 완료\n")

    generate_domain_data(
        sample_count=args.samples,
        order_count=args.orders,
        inventory_count=args.inventories,
        queue_count=args.queue,
    )

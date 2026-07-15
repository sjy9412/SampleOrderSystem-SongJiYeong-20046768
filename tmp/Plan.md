# STEP 6 — ProductionLine 모델 TDD Plan

## 목표 (Goal)

`models/production_line.py` 구현 및 `tests/test_production_line.py` 작성.

FIFO 생산 큐를 DB(`production_queue` 컬렉션)로 관리하고,
생산량 산정 및 완료 처리(재고 증가 + 주문 CONFIRMED 전환)를 담당한다.

---

## 부가 변경: OrderModel

`complete()` 내부에서 PRODUCING → CONFIRMED 전환이 필요하다.
현재 `OrderModel.confirm()`은 RESERVED → CONFIRMED만 지원하므로
`OrderModel`에 `confirm_production(order_id)` 메서드를 추가한다.
(메서드 1개 추가, 기존 로직 변경 없음)

---

## 구현 파일

| 파일 | 변경 종류 |
|------|-----------|
| `models/order.py` | `confirm_production()` 메서드 추가 |
| `models/production_line.py` | 신규 생성 |
| `tests/test_production_line.py` | 신규 생성 |

---

## 생산량 산정 공식

```
부족분      = 주문 수량 - 현재 재고
실 생산량   = ceil(부족분 / 수율)
총 생산시간 = 평균 생산시간 × 실 생산량
```

---

## 테스트 케이스 목록

### calculate_production (순수 계산 — DB 불필요)

| 테스트 이름 | 검증 내용 |
|-------------|-----------|
| `test_calculate_production_returns_correct_values` | shortage=90, yield=0.9, avg_time=2.0 → actual_qty=100, total_time=200.0 |
| `test_calculate_production_uses_ceil` | shortage=10, yield=0.3 → ceil(10/0.3)=34 |

### enqueue / get_queue / get_current

| 테스트 이름 | 검증 내용 |
|-------------|-----------|
| `test_enqueue_adds_order_to_queue` | enqueue 후 get_queue() 에 해당 order_id 포함 |
| `test_get_queue_returns_orders_in_fifo_order` | enqueue 두 건 → get_queue() 순서 FIFO 보장 |
| `test_get_current_returns_first_in_queue` | enqueue 두 건 → get_current() 첫 번째 항목 반환 |
| `test_get_current_returns_none_when_queue_is_empty` | 빈 큐 → None |

### complete

| 테스트 이름 | 검증 내용 |
|-------------|-----------|
| `test_complete_increases_inventory` | complete 후 재고가 실 생산량만큼 증가 |
| `test_complete_confirms_order` | complete 후 주문 상태 CONFIRMED |
| `test_complete_removes_order_from_queue` | complete 후 get_queue() 에서 해제됨 |

---

## 구현 방향 (최소한의 코드)

```python
# models/production_line.py

import math
from db import json_store as store
from models.base import ObservableModel

COLLECTION = "production_queue"


class ProductionLine(ObservableModel):

    def __init__(self, order_model, inventory_model, sample_model):
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
```

```python
# models/order.py 에 추가
def confirm_production(self, order_id: str) -> dict:
    return self._transition(order_id, "PRODUCING", "CONFIRMED")
```

---

## 예상 실패 이유

테스트 작성 시 `models/production_line.py` 가 존재하지 않으므로
`ImportError` 로 즉시 실패한다.

---

## 체크리스트

- [ ] Plan.md 사용자 승인
- [ ] `tests/test_production_line.py` 작성 → RED 확인
- [ ] `models/production_line.py` + `OrderModel.confirm_production()` 구현 → GREEN 확인
- [ ] REVIEW → 커밋

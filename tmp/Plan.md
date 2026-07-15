# Plan — STEP 4: Inventory (재고) 모델

## 목표 (Goal)

`models/inventory.py`에 `InventoryModel`을 구현한다.  
시료별 재고 수량을 DB에 영속화하고, 주문 대비 재고 상태를 판단하는 기능을 제공한다.

---

## 데이터 구조

컬렉션명: `"inventories"`

| 필드 | 타입 | 설명 |
|------|------|------|
| `sample_id` | str | 시료 ID (고유, 검색 키) |
| `quantity` | int | 현재 재고 수량 |

> `id`, `created_at`, `updated_at`는 `json_store.create()`가 자동 부여

---

## 구현 메서드

| 메서드 | 설명 |
|--------|------|
| `get_stock(sample_id)` | 특정 시료의 현재 재고 수량 반환 (없으면 0) |
| `get_all_stocks()` | 전체 시료 재고 레코드 목록 반환 |
| `is_sufficient(sample_id, quantity)` | 재고 >= quantity 이면 True |
| `decrease(sample_id, quantity)` | 재고 차감. 재고 부족 시 ValueError |
| `increase(sample_id, quantity)` | 재고 증가. 레코드 없으면 신규 생성 |
| `get_status(sample_id, ordered_quantity)` | `"여유"` / `"부족"` / `"고갈"` 반환 |

**상태 판단 규칙**
- `"고갈"`: `quantity == 0`
- `"부족"`: `0 < quantity < ordered_quantity`
- `"여유"`: `quantity >= ordered_quantity`

---

## 작성할 테스트 (tests/test_inventory_model.py)

```
1. test_get_stock_returns_zero_for_unknown_sample
   -> 재고 레코드 없는 시료 조회 시 0 반환

2. test_increase_creates_stock_record
   -> increase 후 get_stock이 해당 수량 반환

3. test_increase_accumulates_quantity
   -> 두 번 increase 하면 합계가 반환됨

4. test_decrease_reduces_stock
   -> decrease 후 get_stock이 줄어든 수량 반환

5. test_decrease_raises_when_insufficient
   -> 재고보다 많은 양 차감 시 ValueError

6. test_is_sufficient_returns_true_when_enough
   -> quantity >= ordered_quantity -> True

7. test_is_sufficient_returns_false_when_not_enough
   -> quantity < ordered_quantity -> False

8. test_get_all_stocks_returns_all_records
   -> 여러 시료 increase 후 get_all_stocks() 결과 수 일치

9. test_get_status_returns_여유_when_sufficient
   -> quantity >= ordered_quantity -> "여유"

10. test_get_status_returns_부족_when_low
    -> 0 < quantity < ordered_quantity -> "부족"

11. test_get_status_returns_고갈_when_zero
    -> quantity == 0 -> "고갈"
```

---

## 예상 실패 이유

`models/inventory.py`가 존재하지 않으므로 `ImportError`로 실패한다.

---

## 구현 방향 (GREEN 단계)

```python
# models/inventory.py
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
```

---

## 체크리스트

- [ ] Plan.md 사용자 승인
- [ ] `tests/test_inventory_model.py` 작성 -> RED 확인
- [ ] `models/inventory.py` 구현 -> GREEN 확인
- [ ] REVIEW -> 커밋

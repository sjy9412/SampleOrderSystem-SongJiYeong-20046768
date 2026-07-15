# Plan — STEP 3: Order 모델

## 목표 (goal)

`models/order.py`에 `OrderModel` 클래스를 구현한다.  
주문 생성(RESERVED)부터 상태 전이(PRODUCING / CONFIRMED / RELEASE / REJECTED)까지의 도메인 로직을 커버한다.

---

## 작성할 테스트 (`tests/test_order_model.py`)

### 픽스처

```python
@pytest.fixture(autouse=True)
def clean_db():
    store.reset("orders")
    yield
    store.reset("orders")

@pytest.fixture
def model():
    return OrderModel()
```

### 테스트 목록

| # | 테스트명 | 검증 내용 |
|---|----------|-----------|
| 1 | `test_reserve_returns_order_with_id` | `reserve()` 반환 객체에 id, sample_id, customer_name, quantity, status=="RESERVED" 포함 |
| 2 | `test_reserve_emits_added_event` | `reserve()` 호출 시 `EventType.ADDED` 이벤트 발행, payload에 주문 포함 |
| 3 | `test_get_reserved_returns_only_reserved_orders` | RESERVED 주문만 반환, 다른 상태는 제외 |
| 4 | `test_get_by_status_returns_matching_orders` | 지정 상태의 주문 목록 반환 |
| 5 | `test_get_by_id_returns_correct_order` | ID로 단건 조회 |
| 6 | `test_get_by_id_returns_none_for_unknown_id` | 없는 ID → None 반환 |
| 7 | `test_confirm_changes_status_to_confirmed` | `confirm()` → status == "CONFIRMED" |
| 8 | `test_reject_changes_status_to_rejected` | `reject()` → status == "REJECTED" |
| 9 | `test_set_producing_changes_status_to_producing` | `set_producing()` → status == "PRODUCING" |
| 10 | `test_release_changes_status_to_release` | `release()` → status == "RELEASE" |
| 11 | `test_confirm_only_works_on_reserved_order` | RESERVED가 아닌 주문에 `confirm()` → ValueError |
| 12 | `test_reject_only_works_on_reserved_order` | RESERVED가 아닌 주문에 `reject()` → ValueError |
| 13 | `test_set_producing_only_works_on_reserved_order` | RESERVED가 아닌 주문에 `set_producing()` → ValueError |
| 14 | `test_release_only_works_on_confirmed_order` | CONFIRMED가 아닌 주문에 `release()` → ValueError |

---

## 예상 실패 이유

`models/order.py` 파일이 존재하지 않으므로 import 시점에 `ModuleNotFoundError` 발생.

---

## 구현 방향 (최소한의 코드)

**`models/order.py`**

```python
class OrderModel(ObservableModel):
    COLLECTION = "orders"

    def reserve(self, sample_id, customer_name, quantity) -> dict:
        record = store.create(self.COLLECTION, {
            "sample_id": sample_id,
            "customer_name": customer_name,
            "quantity": quantity,
            "status": "RESERVED",
        })
        self._notify(ModelEvent(EventType.ADDED, record))
        return record

    def get_reserved(self) -> list[dict]:
        return store.read_all(self.COLLECTION, status="RESERVED")

    def get_by_status(self, status: str) -> list[dict]:
        return store.read_all(self.COLLECTION, status=status)

    def get_by_id(self, order_id: str) -> dict | None:
        return store.read_one(self.COLLECTION, order_id)

    def _transition(self, order_id, from_status, to_status):
        order = store.read_one(self.COLLECTION, order_id)
        if order is None or order["status"] != from_status:
            raise ValueError(f"주문 {order_id}의 상태가 {from_status}가 아닙니다.")
        return store.update(self.COLLECTION, order_id, {"status": to_status})

    def confirm(self, order_id):       return self._transition(order_id, "RESERVED",  "CONFIRMED")
    def reject(self, order_id):        return self._transition(order_id, "RESERVED",  "REJECTED")
    def set_producing(self, order_id): return self._transition(order_id, "RESERVED",  "PRODUCING")
    def release(self, order_id):       return self._transition(order_id, "CONFIRMED", "RELEASE")
```

**이벤트 타입**: `models/base.py`의 `EventType`에 이미 `ADDED`가 있으므로 추가 불필요.

---

## 범위 제한

- `models/order.py`만 생성
- View / Controller / 다른 모델 수정 없음
- STEP 3 기능만 구현 (STEP 5~6 연동 로직 없음)

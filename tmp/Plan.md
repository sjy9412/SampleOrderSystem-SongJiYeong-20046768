# TDD Plan — STEP 5: 주문 승인/거절 View / Controller

## Goal

`OrderController` + `OrderView` 를 구현한다.

- 주문 접수(예약): RESERVED 상태 주문 생성
- 승인/거절 메뉴: RESERVED 목록 표시 후 처리
- 승인 + 재고 충분 → CONFIRMED + 재고 차감
- 승인 + 재고 부족 → 안내 후 재확인 → 승인 시 PRODUCING + enqueue, 거절 시 REJECTED
- 직접 거절 → REJECTED

---

## 작성할 테스트 (`tests/test_order_controller.py`)

### 공통 준비

```python
@pytest.fixture(autouse=True)
def clean_db():
    store.reset("orders")
    store.reset("inventories")
    yield
    store.reset("orders")
    store.reset("inventories")
```

**stub 설계**

- `ProductionLineStub`: `enqueue(order_id)` 호출 목록 기록
- `OrderViewStub`:
  - `set_inputs(*values)` → `get_menu_choice`, `get_order_input`, `get_order_id`, `get_approve_or_reject` 순서대로 소비
  - `shown_orders`: `show_orders` 에 전달된 목록 캡처
  - `stock_insufficient_shown`: `show_stock_insufficient` 호출 여부

---

### TC-1: 주문 접수 → RESERVED 주문 생성

```
입력 시퀀스: 메뉴 "1" → get_order_input → (sample-1, 홍길동, 5) → 메뉴 "0"
기대:
  - order_model.get_reserved() 길이 == 1
  - sample_id == "sample-1", customer_name == "홍길동", quantity == 5, status == "RESERVED"
```

### TC-2: 승인/거절 메뉴 진입 시 RESERVED 목록 표시

```
사전: RESERVED 주문 2건 생성
입력 시퀀스: 메뉴 "2" → get_order_id → "" (빈값, 조기 종료) → 메뉴 "0"
기대:
  - view.shown_orders 길이 == 2
  - 모두 status == "RESERVED"
```

### TC-3: 승인 + 재고 충분 → CONFIRMED + 재고 차감

```
사전: inventory_model.increase("sample-1", 10), 주문 수량 5
입력 시퀀스: 메뉴 "2" → order_id → "승인" → 메뉴 "0"
기대:
  - order.status == "CONFIRMED"
  - inventory_model.get_stock("sample-1") == 5
```

### TC-4: 승인 + 재고 부족 + 재확인 승인 → PRODUCING + enqueue

```
사전: inventory_model.increase("sample-1", 2), 주문 수량 5
입력 시퀀스: 메뉴 "2" → order_id → "승인" → (재고 부족 안내) → "승인" → 메뉴 "0"
기대:
  - order.status == "PRODUCING"
  - production_line.enqueued 에 order_id 포함
  - view.stock_insufficient_shown == True
```

### TC-5: 승인 + 재고 부족 + 재확인 거절 → REJECTED

```
사전: inventory_model.increase("sample-1", 2), 주문 수량 5
입력 시퀀스: 메뉴 "2" → order_id → "승인" → (재고 부족 안내) → "거절" → 메뉴 "0"
기대:
  - order.status == "REJECTED"
  - view.stock_insufficient_shown == True
```

### TC-6: 거절 → REJECTED

```
사전: RESERVED 주문 1건
입력 시퀀스: 메뉴 "2" → order_id → "거절" → 메뉴 "0"
기대:
  - order.status == "REJECTED"
```

---

## 예상 실패 이유

`controllers/order_controller.py`, `views/order_view.py` 가 존재하지 않아
`ImportError` / `ModuleNotFoundError` 로 실패.

---

## 구현 방향 (최소한의 코드)

### `views/order_view.py`

- `__init__(model)`: `model.subscribe(self)`
- `show_menu()`: 메뉴 문자열 출력
- `get_menu_choice()` → `input()`
- `get_order_input()` → `(sample_id, customer_name, quantity)` 튜플
- `get_order_id(action)` → `str`
- `get_approve_or_reject()` → `"승인"` or `"거절"`
- `show_orders(orders)`: 목록 테이블 출력
- `show_stock_insufficient(stock, required)`: 재고 부족 안내
- `show_error(message)`, `show_invalid_input()`, `show_exit()`, `on_model_changed(event)`

### `controllers/order_controller.py`

- `__init__(order_model, inventory_model, production_line, view)`
- `run()`: while 루프, 0→종료, 1→_handle_reserve, 2→_handle_approve_reject
- `_handle_reserve()`: `view.get_order_input()` → `order_model.reserve()`
- `_handle_approve_reject()`:
  1. `order_model.get_reserved()` → `view.show_orders()`
  2. `view.get_order_id("처리")` → 빈값이면 return
  3. `order_model.get_by_id()` → None이면 `view.show_error()` + return
  4. `view.get_approve_or_reject()`
     - `"거절"` → `order_model.reject()`
     - `"승인"` + 재고 충분 → `inventory_model.decrease()` + `order_model.confirm()`
     - `"승인"` + 재고 부족 → `view.show_stock_insufficient()` → 재확인
       - `"승인"` → `order_model.set_producing()` + `production_line.enqueue()`
       - `"거절"` → `order_model.reject()`

---

## 체크리스트

- [ ] Plan.md 사용자 승인
- [ ] `tests/test_order_controller.py` 작성 → RED 확인
- [ ] `views/order_view.py`, `controllers/order_controller.py` 구현 → GREEN 확인
- [ ] REVIEW → 커밋

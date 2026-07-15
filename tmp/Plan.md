# TDD Plan — STEP 5: 주문 승인/거절 View / Controller

## Goal

`OrderController` + `OrderView` 를 구현한다.

- 주문 접수(예약), 접수된 주문 목록, 주문 승인, 주문 거절 기능
- 승인 시 재고 충분 → CONFIRMED + 재고 차감, 부족 → PRODUCING + enqueue

---

## 작성할 테스트 (`tests/test_order_controller.py`)

### TC-1: 주문 접수 → RESERVED 주문 생성
```
입력: sample_id, customer_name, quantity
기대: OrderModel에 RESERVED 상태 주문이 생성된다
```

### TC-2: 접수된 주문 목록 → RESERVED 주문만 반환
```
입력: 미리 reserve된 주문들
기대: view.show_orders가 RESERVED 목록을 받아 호출된다
```

### TC-3: 승인 — 재고 충분 → CONFIRMED + 재고 차감
```
입력: 재고(10) >= 주문 수량(5)
기대: order.status == "CONFIRMED", inventory 차감됨
```

### TC-4: 승인 — 재고 부족 → PRODUCING + enqueue
```
입력: 재고(2) < 주문 수량(5)
기대: order.status == "PRODUCING", production_line.enqueue(order_id) 호출됨
```

### TC-5: 거절 → REJECTED 전환
```
입력: RESERVED 상태 주문 ID
기대: order.status == "REJECTED"
```

---

## 예상 실패 이유

`controllers/order_controller.py`, `views/order_view.py` 가 존재하지 않아 `ImportError`.

---

## 구현 방향 (최소한의 코드)

### `views/order_view.py`
- `__init__(model)`: `model.subscribe(self)`
- `show_menu()`: 메뉴 문자열 출력
- `get_menu_choice()`: `input()`
- `get_order_input()` → `(sample_id, customer_name, quantity)`
- `get_order_id(action)` → `str`
- `show_orders(orders)`: 목록 출력
- `show_error(message)`, `show_invalid_input()`, `show_exit()`, `on_model_changed(event)`

### `controllers/order_controller.py`
- `__init__(order_model, inventory_model, production_line, view)`
- `run()`: while 루프, 메뉴 선택에 따라 핸들러 호출
- `_handle_reserve()`: `view.get_order_input()` → `model.reserve()`
- `_handle_list()`: `model.get_reserved()` → `view.show_orders()`
- `_handle_approve()`: `view.get_order_id()` → 재고 판단 → confirm 또는 set_producing + enqueue
- `_handle_reject()`: `view.get_order_id()` → `model.reject()`

### 테스트용 stub
- `ProductionLineStub`: `enqueue(order_id)` 호출 기록
- `OrderViewStub`: 미리 지정된 입력 반환, 출력 캡처

---

## 체크리스트

- [ ] Plan.md 사용자 승인
- [ ] `tests/test_order_controller.py` 작성 → RED 확인
- [ ] `views/order_view.py`, `controllers/order_controller.py` 구현 → GREEN 확인
- [ ] REVIEW → 커밋

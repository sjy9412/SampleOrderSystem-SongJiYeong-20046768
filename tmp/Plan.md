# STEP 7 — 생산 라인 View / Controller TDD Plan

## 목표

`ProductionController` + `ProductionView` 구현.  
메뉴 1 → 현재 생산 현황 표시, 메뉴 2 → 대기 큐 목록 표시.

---

## 변경 파일

| 파일 | 유형 |
|------|------|
| `tests/test_production_controller.py` | 신규 (테스트) |
| `views/production_view.py` | 신규 |
| `controllers/production_controller.py` | 신규 |
| `models/production_line.py` | 수정 (메서드 2개 추가) |

---

## 설계 결정

`ProductionController(production_line, view)` — PLAN.md STEP 10 API 그대로 유지.  
현황 조회에 필요한 시료명·실생산량·총생산시간 계산 책임은 `ProductionLine`에 새 메서드 2개로 위임.

| 메서드 | 반환 |
|--------|------|
| `ProductionLine.get_current_info()` | `dict \| None` — order_id, sample_name, quantity, actual_qty, total_time |
| `ProductionLine.get_queue_info()` | `list[dict]` — position, order_id, sample_name, customer_name, quantity |

두 메서드는 기존 `_order_model`, `_inventory_model`, `_sample_model`을 활용.  
STEP 6 기존 테스트는 영향 없음.

---

## TDD 사이클

### Cycle 1 — 현재 생산 현황 조회 (주문 있음)

**Goal**: 메뉴 1 선택 시 `view.show_current()`에 주문 ID·시료명·수량·실생산량·총생산시간이 전달된다.

```python
def test_current_shows_production_info(
    controller, production_line, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("AAA", 2.0, 0.8)
    inventory_model.increase(sample["id"], 3)
    order = order_model.reserve(sample["id"], "홍길동", 10)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    view.set_inputs("1", "0")
    controller.run()

    # 부족분=7, 실생산량=ceil(7/0.8)=9, 총시간=2.0×9=18.0
    assert view.shown_current["order_id"] == order["id"]
    assert view.shown_current["sample_name"] == "AAA"
    assert view.shown_current["quantity"] == 10
    assert view.shown_current["actual_qty"] == 9
    assert view.shown_current["total_time"] == 18.0
```

**예상 실패 이유**: `ProductionController`, `ProductionView`, `ProductionLine.get_current_info()` 미존재 → ImportError

---

### Cycle 2 — 현재 생산 현황 조회 (큐 비어있음)

**Goal**: 큐가 비어있을 때 메뉴 1 선택 시 `view.show_no_current()`가 호출된다.

```python
def test_current_when_empty_shows_no_current(controller, view):
    view.set_inputs("1", "0")
    controller.run()

    assert view.shown_current is None
    assert view.no_current_shown is True
```

**예상 실패 이유**: 동일

---

### Cycle 3 — 대기 주문 목록 조회

**Goal**: 메뉴 2 선택 시 enqueue된 주문들이 순번과 함께 `view.show_queue()`로 전달된다.

```python
def test_queue_shows_waiting_orders_in_order(
    controller, production_line, order_model, sample_model, view
):
    sample = sample_model.add("AAA", 2.0, 0.8)
    order1 = order_model.reserve(sample["id"], "홍길동", 5)
    order2 = order_model.reserve(sample["id"], "이순신", 3)
    order_model.set_producing(order1["id"])
    order_model.set_producing(order2["id"])
    production_line.enqueue(order1["id"])
    production_line.enqueue(order2["id"])

    view.set_inputs("2", "0")
    controller.run()

    assert len(view.shown_queue) == 2
    assert view.shown_queue[0]["position"] == 1
    assert view.shown_queue[0]["order_id"] == order1["id"]
    assert view.shown_queue[0]["sample_name"] == "AAA"
    assert view.shown_queue[0]["customer_name"] == "홍길동"
    assert view.shown_queue[1]["position"] == 2
    assert view.shown_queue[1]["customer_name"] == "이순신"
```

**예상 실패 이유**: 동일

---

## 구현 방향 (GREEN 단계)

### `models/production_line.py` 추가 메서드

```python
def get_current_info(self) -> dict | None:
    current = self.get_current()
    if current is None:
        return None
    order = self._order_model.get_by_id(current["order_id"])
    sample = self._sample_model.get_by_id(order["sample_id"])
    stock = self._inventory_model.get_stock(order["sample_id"])
    shortage = max(0, order["quantity"] - stock)
    actual_qty, total_time = self.calculate_production(
        shortage, sample["yield_rate"], sample["avg_production_time"]
    )
    return {
        "order_id": order["id"],
        "sample_name": sample["name"],
        "quantity": order["quantity"],
        "actual_qty": actual_qty,
        "total_time": total_time,
    }

def get_queue_info(self) -> list[dict]:
    result = []
    for i, item in enumerate(self.get_queue(), 1):
        order = self._order_model.get_by_id(item["order_id"])
        sample = self._sample_model.get_by_id(order["sample_id"])
        result.append({
            "position": i,
            "order_id": order["id"],
            "sample_name": sample["name"],
            "customer_name": order["customer_name"],
            "quantity": order["quantity"],
        })
    return result
```

### `controllers/production_controller.py`

```python
class ProductionController:
    def __init__(self, production_line, view) -> None: ...
    def run(self) -> None: ...              # 메뉴 루프 (1/2/0)
    def _handle_current(self) -> None: ... # get_current_info() → show_current / show_no_current
    def _handle_queue(self) -> None: ...   # get_queue_info() → show_queue
```

### `views/production_view.py`

```python
class ProductionView:
    MENU = "\n[생산 라인]\n1. 생산 현황 조회\n2. 대기 주문 목록\n0. 뒤로\n"
    def show_current(self, info: dict) -> None: ...
    def show_no_current(self) -> None: ...
    def show_queue(self, items: list[dict]) -> None: ...
```

---

## 체크리스트

- [ ] Plan.md 사용자 승인
- [ ] `tests/test_production_controller.py` 작성 → RED 확인
- [ ] `models/production_line.py` 메서드 추가 + `views/production_view.py` + `controllers/production_controller.py` 구현 → GREEN 확인
- [ ] REVIEW → 커밋

# TDD Plan — 수량 단위(ea) · 시간 단위(min) 표시

## Goal

View 레이어의 레이블·값에 단위를 명시한다.

| 위치 | 현재 | 변경 후 |
|------|------|---------|
| `sample_view.get_sample_input()` 프롬프트 | `"평균 생산시간(시간):"` | `"평균 생산시간(min):"` |
| `sample_view.show_samples()` 컬럼 헤더 | `"평균 생산시간(h)"` | `"평균 생산시간(min)"` |
| `order_view.get_order_input()` 프롬프트 | `"수량:"` | `"수량(ea):"` |
| `order_view.show_orders()` 수량 값 | `"5"` | `"5 ea"` |
| `production_view.show_current()` 총 생산시간 값 | `"2.5h"` | `"2.5 min"` |
| `production_view.show_queue()` 수량 값 | `"5"` | `"5 ea"` |

---

## 작성할 테스트

### `tests/test_sample_view.py` (신규)

```python
import pytest
from models.sample import SampleModel
from views.sample_view import SampleView


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("samples")
    yield
    store.reset("samples")


@pytest.fixture
def view():
    model = SampleModel()
    return SampleView(model)


# TC-1: show_samples 컬럼 헤더에 "min" 포함
def test_show_samples_uses_min_unit_in_column_header(view, capsys):
    samples = [{"id": "S-001", "name": "TestChip", "avg_production_time": 2.5, "yield_rate": 0.95}]
    view.show_samples(samples, {})
    output = capsys.readouterr().out
    assert "min" in output


# TC-2: get_sample_input 프롬프트에 "min" 포함
def test_get_sample_input_prompt_contains_min(view, capsys, monkeypatch):
    inputs = iter(["TestChip", "2.5", "0.95"])
    monkeypatch.setattr("builtins.input", lambda: next(inputs))
    view.get_sample_input()
    output = capsys.readouterr().out
    assert "min" in output
```

### `tests/test_order_view.py` (신규)

```python
import pytest
from models.order import OrderModel
from views.order_view import OrderView


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("orders")
    yield
    store.reset("orders")


@pytest.fixture
def view():
    model = OrderModel()
    return OrderView(model)


# TC-3: show_orders 수량 값에 "ea" 포함
def test_show_orders_displays_ea_unit(view, capsys):
    orders = [{"id": "O-001", "customer_name": "홍길동", "quantity": 5, "status": "RESERVED"}]
    view.show_orders(orders)
    output = capsys.readouterr().out
    assert "ea" in output


# TC-4: get_order_input 프롬프트에 "ea" 포함
def test_get_order_input_prompt_contains_ea(view, capsys, monkeypatch):
    inputs = iter(["S-001", "홍길동", "5"])
    monkeypatch.setattr("builtins.input", lambda: next(inputs))
    view.get_order_input()
    output = capsys.readouterr().out
    assert "ea" in output
```

### `tests/test_production_view.py` (신규)

```python
import pytest
from models.production_line import ProductionLine
from views.production_view import ProductionView


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("orders")
    store.reset("samples")
    store.reset("production_queue")
    yield
    store.reset("orders")
    store.reset("samples")
    store.reset("production_queue")


@pytest.fixture
def view():
    model = ProductionLine()
    return ProductionView(model)


# TC-5: show_current 총 생산시간 값에 "min" 포함
def test_show_current_displays_min_unit(view, capsys):
    info_data = {
        "order_id": "O-001",
        "sample_name": "TestChip",
        "quantity": 5,
        "actual_qty": 6,
        "total_time": 12.0,
    }
    view.show_current(info_data)
    output = capsys.readouterr().out
    assert "min" in output


# TC-6: show_queue 수량 값에 "ea" 포함
def test_show_queue_displays_ea_unit(view, capsys):
    items = [{
        "position": 1,
        "order_id": "O-001",
        "sample_name": "TestChip",
        "customer_name": "홍길동",
        "quantity": 5,
    }]
    view.show_queue(items)
    output = capsys.readouterr().out
    assert "ea" in output
```

---

## 예상 실패 이유

| 테스트 | 실패 원인 |
|--------|-----------|
| TC-1 | 컬럼 키가 `"평균 생산시간(h)"` → "min" 없음 |
| TC-2 | 프롬프트가 `"평균 생산시간(시간):"` → "min" 없음 |
| TC-3 | 수량이 `str(o["quantity"])` → "ea" 없음 |
| TC-4 | 프롬프트가 `"수량:"` → "ea" 없음 |
| TC-5 | 총 생산시간이 `f"{total_time:.1f}h"` → "min" 없음 |
| TC-6 | 수량이 `str(item["quantity"])` → "ea" 없음 |

---

## 구현 방향 (최소한의 변경)

### `views/sample_view.py`

```python
# get_sample_input()
avg_time = float(prompt_input("평균 생산시간(min):"))    # "(시간)" → "(min)"

# show_samples()
"평균 생산시간(min)": f"{s['avg_production_time']:.1f}",  # "(h)" → "(min)"
```

### `views/order_view.py`

```python
# get_order_input()
quantity = int(prompt_input("수량(ea):"))               # "수량:" → "수량(ea):"

# show_orders()
"수량": f"{o['quantity']} ea",                          # str → "N ea"
```

### `views/production_view.py`

```python
# show_current()
t.add_row("총 생산시간", f"{info_data['total_time']:.1f} min")  # "h" → "min"

# show_queue()
"수량": f"{item['quantity']} ea",                       # str → "N ea"
```

---

## 영향 범위

| 파일 | 변경 내용 |
|------|-----------|
| `tests/test_sample_view.py` | 신규: TC-1, TC-2 |
| `tests/test_order_view.py` | 신규: TC-3, TC-4 |
| `tests/test_production_view.py` | 신규: TC-5, TC-6 |
| `views/sample_view.py` | 프롬프트·컬럼 레이블 "min" 적용 |
| `views/order_view.py` | 프롬프트 "ea", 수량 값 "N ea" |
| `views/production_view.py` | 총 생산시간 "min", 수량 값 "N ea" |
| `docs/PRD.md` | 이미 반영 완료 |

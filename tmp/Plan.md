# TDD Plan — 메인화면 시스템 현황 대시보드 + 선택 프롬프트

## 목표

1. `prompt_choice()` 출력을 `선택 >` 형식으로 변경
2. 메인 메뉴 루프마다 **시스템 현황 패널** 표시
   - 헤더: `시스템 현황  YYYY-MM-DD HH:MM:SS`
   - 내용: `등록 시료 N종   총 재고 Nea   전체 주문 N건   생산라인 N건 대기`

---

## Cycle 1 — `prompt_choice` 프롬프트 형식 (`선택 >`)

### 작성할 테스트 (`tests/test_display.py` 신규)

```python
def test_prompt_choice_shows_arrow_format(capsys, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "1")
    from views.display import prompt_choice
    prompt_choice()
    out = capsys.readouterr().out
    assert "선택 >" in out
```

### 예상 실패 이유
현재 `prompt_choice`는 `"선택"` 뒤에 `>`를 출력하지 않으므로 assertion 실패.

### 구현 방향 (`views/display.py`)

```python
def prompt_choice(label: str = "선택") -> str:
    console.print(f"\n  [bold cyan]{label} >[/bold cyan] ", end="")
    return input().strip()
```

---

## Cycle 2 — 시스템 현황 대시보드

### 영향 파일

| 파일 | 변경 내용 |
|------|----------|
| `models/order.py` | `get_all()` 메서드 추가 (전체 주문 수 조회용) |
| `controllers/main_controller.py` | 생성자에 모델 4개 키워드 인수 추가, 루프마다 `_show_dashboard()` 호출 |
| `app.py` | `MainController` 생성 시 모델 전달 |

### 작성할 테스트 (`tests/test_main_controller.py` — 테스트 추가)

```python
class FakeSampleModel:
    def get_all(self): return [{"id": "S-001"}, {"id": "S-002"}]

class FakeInventoryModel:
    def get_all_stocks(self): return [{"quantity": 10}, {"quantity": 5}]

class FakeOrderModel:
    def get_all(self): return [{"id": "o1"}, {"id": "o2"}, {"id": "o3"}]

class FakeProductionLine:
    def get_queue(self): return [{"order_id": "o1"}]


def test_dashboard_shows_sample_count(capsys):
    ctrl = MainController(
        [],
        sample_model=FakeSampleModel(),
        inventory_model=FakeInventoryModel(),
        order_model=FakeOrderModel(),
        production_line=FakeProductionLine(),
    )
    with patch("builtins.input", return_value="0"):
        ctrl.run()
    assert "2종" in capsys.readouterr().out


def test_dashboard_shows_total_stock(capsys):
    ctrl = MainController(
        [],
        sample_model=FakeSampleModel(),
        inventory_model=FakeInventoryModel(),
        order_model=FakeOrderModel(),
        production_line=FakeProductionLine(),
    )
    with patch("builtins.input", return_value="0"):
        ctrl.run()
    assert "15ea" in capsys.readouterr().out


def test_dashboard_shows_order_count(capsys):
    ctrl = MainController(
        [],
        sample_model=FakeSampleModel(),
        inventory_model=FakeInventoryModel(),
        order_model=FakeOrderModel(),
        production_line=FakeProductionLine(),
    )
    with patch("builtins.input", return_value="0"):
        ctrl.run()
    assert "3건" in capsys.readouterr().out


def test_dashboard_shows_production_queue_count(capsys):
    ctrl = MainController(
        [],
        sample_model=FakeSampleModel(),
        inventory_model=FakeInventoryModel(),
        order_model=FakeOrderModel(),
        production_line=FakeProductionLine(),
    )
    with patch("builtins.input", return_value="0"):
        ctrl.run()
    assert "1건 대기" in capsys.readouterr().out
```

### 예상 실패 이유
`MainController.__init__`가 키워드 인수를 받지 않아 `TypeError`.

### 구현 방향

**`models/order.py` 추가:**
```python
def get_all(self) -> list[dict]:
    return store.read_all(self.COLLECTION)
```

**`controllers/main_controller.py` 변경:**
```python
def __init__(self, sub_controllers, *, sample_model=None,
             inventory_model=None, order_model=None, production_line=None):
    ...

def _show_dashboard(self):
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sample_count = len(self._sample_model.get_all()) if self._sample_model else 0
    total_stock  = sum(r["quantity"] for r in self._inventory_model.get_all_stocks()) \
                   if self._inventory_model else 0
    order_count  = len(self._order_model.get_all()) if self._order_model else 0
    queue_count  = len(self._production_line.get_queue()) if self._production_line else 0
    # Rich Panel 로 출력
    ...

def run(self):
    console.print(BANNER)
    while True:
        self._show_dashboard()      # ← 추가
        show_menu_panel(...)
        ...
```

**`app.py` 변경:**
```python
return MainController(
    [...],
    sample_model=sample_model,
    inventory_model=inventory_model,
    order_model=order_model,
    production_line=production_line,
)
```

---

## 기존 테스트 호환성

`MainController([])` 처럼 모델 없이 생성하는 기존 테스트는  
키워드 인수의 기본값이 `None`이므로 깨지지 않음.

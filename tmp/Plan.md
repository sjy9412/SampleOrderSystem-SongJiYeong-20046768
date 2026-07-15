# TDD Plan — STEP 10: 메인 메뉴 통합

## 목표 (Goal)

`MainController`와 `create_app()`을 구현해, 모든 하위 컨트롤러를 하나의 메인 루프로 통합한다.

**구현 파일**
- `controllers/main_controller.py` (신규)
- `app.py` (구현 완성)
- `tests/test_main_controller.py` (신규)

**메인 메뉴**
```
[메인 메뉴]
1. 시료 관리
2. 주문 (접수 / 승인 / 거절)
3. 모니터링
4. 출고 처리
5. 생산 라인
0. 종료
```

---

## 테스트 케이스 (`tests/test_main_controller.py`)

### TC-1: "0" 입력 시 루프 종료

```python
def test_exits_on_zero():
    ctrl = MainController([])
    with patch("builtins.input", return_value="0"):
        ctrl.run()  # 반환되면 통과, 무한루프면 타임아웃
```

예상 실패 이유: `MainController` 미존재 → `ImportError`

---

### TC-2: "1" 입력 시 첫 번째 sub-controller의 run() 호출

```python
class StubController:
    def __init__(self):
        self.called = False
    def run(self):
        self.called = True

def test_dispatches_to_first_sub_controller():
    stub = StubController()
    ctrl = MainController([stub])
    with patch("builtins.input", side_effect=["1", "0"]):
        ctrl.run()
    assert stub.called
```

예상 실패 이유: `MainController` 미존재 → `ImportError`

---

### TC-3: 유효하지 않은 입력 시 "잘못된" 메시지 출력

```python
def test_invalid_input_shows_invalid_message():
    ctrl = MainController([])
    output = []
    with patch("builtins.input", side_effect=["9", "0"]):
        with patch("builtins.print", side_effect=lambda *a, **k: output.append(" ".join(str(x) for x in a))):
            ctrl.run()
    assert any("잘못된" in line for line in output)
```

예상 실패 이유: `MainController` 미존재 → `ImportError`

---

### TC-4: `create_app()`이 `run()` 메서드를 가진 객체 반환

```python
def test_create_app_returns_object_with_run():
    from app import create_app
    app = create_app()
    assert hasattr(app, "run") and callable(app.run)
```

예상 실패 이유: `create_app()` → `NotImplementedError`

---

## 구현 방향 (최소 코드)

### `controllers/main_controller.py`

```python
class MainController:
    MENU = (
        "\n[메인 메뉴]\n"
        "1. 시료 관리\n"
        "2. 주문 (접수 / 승인 / 거절)\n"
        "3. 모니터링\n"
        "4. 출고 처리\n"
        "5. 생산 라인\n"
        "0. 종료\n"
    )

    def __init__(self, sub_controllers: list) -> None:
        self._controllers = sub_controllers

    def run(self) -> None:
        while True:
            print(self.MENU)
            choice = input("선택: ").strip()
            if choice == "0":
                print("시스템을 종료합니다.")
                break
            if choice.isdigit() and 1 <= int(choice) <= len(self._controllers):
                self._controllers[int(choice) - 1].run()
            else:
                print("잘못된 입력입니다.")
```

### `app.py`

```python
def create_app(view_type: str = "table"):
    sample_model    = SampleModel()
    order_model     = OrderModel()
    inventory_model = InventoryModel()
    production_line = ProductionLine(order_model, inventory_model, sample_model)

    sample_ctrl     = SampleController(sample_model, SampleView(sample_model))
    order_ctrl      = OrderController(order_model, inventory_model, production_line, OrderView(order_model))
    monitoring_ctrl = MonitoringController(order_model, inventory_model, sample_model, MonitoringView())
    release_ctrl    = ReleaseController(order_model, ReleaseView(order_model))
    production_ctrl = ProductionController(production_line, ProductionView(production_line))

    return MainController([
        sample_ctrl, order_ctrl, monitoring_ctrl, release_ctrl, production_ctrl
    ])
```

---

## 모킹 전략

- `input()` → `patch("builtins.input")` 으로 대체 (외부 I/O 경계)
- `print()` → `patch("builtins.print")` 으로 대체 (외부 I/O 경계)
- sub-controller → `StubController` 스텁 사용 (화면 I/O 제거 목적)
- `create_app()` 테스트: 실제 객체 조립, `run()` 호출 가능 여부만 검증

---

## STEP 10 범위 외 사항 (건드리지 않음)

- 기존 모델/뷰/컨트롤러 파일 수정 없음
- `main.py` 수정 없음 (기존 UTF-8 설정 유지)

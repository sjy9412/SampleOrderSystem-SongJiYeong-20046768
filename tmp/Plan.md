# TDD Plan — STEP 9: 출고 처리 View / Controller

## 목표 (Goal)

CONFIRMED 상태 주문을 출고(RELEASE)로 전환하는 `ReleaseController`와 `ReleaseView`를 구현한다.

**구현 파일**
- `views/release_view.py`
- `controllers/release_controller.py`
- `tests/test_release_controller.py`

**메뉴 구성**
```
[출고 처리]
1. 출고 가능 주문 목록 (CONFIRMED)
2. 출고 처리
0. 뒤로
```

**핵심 로직**
```
def _handle_release(order_id):
    order_model.release(order_id)    # CONFIRMED → RELEASE
```

---

## 테스트 케이스

### TC-1: 메뉴 선택 1 → CONFIRMED 주문 목록 표시

```python
def test_list_confirmed_orders_shows_confirmed_orders():
    # CONFIRMED 주문 2건 + RESERVED 주문 1건 세팅
    # 메뉴 선택 "1" → "0"
    # view.shown_orders 에 CONFIRMED 주문만 2건 포함됨을 검증
```

예상 실패 이유: `ReleaseController`, `ReleaseView` 미존재 → `ModuleNotFoundError`

### TC-2: 메뉴 선택 2 → order_id 입력 → CONFIRMED → RELEASE 전환

```python
def test_release_transitions_confirmed_order_to_release():
    # CONFIRMED 주문 1건 세팅
    # 메뉴 선택 "2" → order_id → "0"
    # 주문 상태가 RELEASE 임을 검증
```

예상 실패 이유: `ReleaseController._handle_release()` 미구현

### TC-3: 존재하지 않거나 CONFIRMED 아닌 주문 ID 출고 시도 → 오류 표시

```python
def test_release_non_confirmed_order_shows_error():
    # RESERVED 상태 주문에 대해 release 시도
    # show_error 가 호출됨을 검증
```

예상 실패 이유: 예외 처리 로직 미구현

---

## 구현 방향 (최소 코드)

### `views/release_view.py`

```python
class ReleaseView:
    MENU = (
        "\n[출고 처리]\n"
        "1. 출고 가능 주문 목록 (CONFIRMED)\n"
        "2. 출고 처리\n"
        "0. 뒤로\n"
    )

    def __init__(self, model) -> None:
        model.subscribe(self)

    def show_menu(self) -> None: print(self.MENU)
    def get_menu_choice(self) -> str: return input("선택: ").strip()
    def get_order_id(self, action: str) -> str: return input(f"{action}할 주문 ID: ").strip()
    def show_orders(self, orders: list[dict]) -> None: ...  # 테이블 출력
    def show_error(self, message: str) -> None: print(f"[오류] {message}")
    def show_invalid_input(self) -> None: print("잘못된 입력입니다.")
    def show_exit(self) -> None: print("뒤로 갑니다.")
    def get_title_input(self) -> str: return ""
    def get_id_input(self, action: str) -> str: return ""
    def on_model_changed(self, event) -> None: pass
```

### `controllers/release_controller.py`

```python
class ReleaseController:
    def __init__(self, order_model, view) -> None:
        self._order = order_model
        self._view = view

    def run(self) -> None:
        while True:
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                break
            elif choice == "1":
                self._handle_list_confirmed()
            elif choice == "2":
                self._handle_release()
            else:
                self._view.show_invalid_input()

    def _handle_list_confirmed(self) -> None:
        orders = self._order.get_by_status("CONFIRMED")
        self._view.show_orders(orders)

    def _handle_release(self) -> None:
        order_id = self._view.get_order_id("출고")
        if not order_id:
            return
        try:
            self._order.release(order_id)
        except (ValueError, KeyError) as e:
            self._view.show_error(str(e))
```

---

## 모킹 전략

- `db.json_store` 실제 사용 (파일 I/O), `autouse` fixture로 DB 초기화
- 내부 레이어(OrderModel)는 실제 객체 사용
- View는 `ReleaseViewStub` 스텁 사용 (화면 I/O 제거)

---

## STEP 9 범위 외 사항 (건드리지 않음)

- `app.py`, `main.py` 통합은 STEP 10에서 진행
- 다른 모델/컨트롤러 수정 없음

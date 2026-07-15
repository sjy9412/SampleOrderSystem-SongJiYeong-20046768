# TDD Plan — 주문 시 시료 ID 존재 여부 검증

## 목표

`ReserveController._handle_reserve()`에서 입력된 시료 ID가 samples 컬렉션에
존재하지 않으면 주문을 생성하지 않고 에러 메시지를 표시한다.

---

## 현재 문제

`ReserveController`는 `order_model`과 `view`만 주입받으며, 시료 ID 유효성 검사 없이
바로 `order_model.reserve()`를 호출한다. 존재하지 않는 시료 ID도 DB에 그대로 저장된다.

---

## Cycle 1 — 유효하지 않은 시료 ID 주문 시 에러 표시

### 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `controllers/order_controller.py` | 생성자에 `sample_model` 추가, 시료 존재 여부 검증 |
| `app.py` | `ReserveController` 생성 시 `sample_model` 전달 |
| `tests/test_order_controller.py` | Stub·픽스처 수정, 신규 테스트 2개 추가 |

### 작성할 테스트 (`tests/test_order_controller.py`)

```python
# OrderViewStub에 추가
def show_error(self, message: str):
    self.last_error = message   # 기존 pass → 기록

# reserve_ctrl 픽스처: sample_model 포함
@pytest.fixture
def sample_model():
    return SampleModel()

@pytest.fixture
def reserve_ctrl(order_model, sample_model, view):
    return ReserveController(order_model, sample_model, view)


# TC-10: 존재하지 않는 시료 ID → 주문 미생성 + 에러 표시
def test_reserve_shows_error_for_nonexistent_sample(reserve_ctrl, order_model, view):
    view.set_inputs(("S-999", "홍길동", 5), "Y")
    reserve_ctrl.run()
    assert len(order_model.get_reserved()) == 0
    assert "시료" in view.last_error


# TC-11: 존재하는 시료 ID → 정상 주문 생성
def test_reserve_succeeds_for_existing_sample(reserve_ctrl, order_model, sample_model, view):
    sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    samples = sample_model.get_all()
    view.set_inputs((samples[0]["id"], "홍길동", 5), "Y")
    reserve_ctrl.run()
    assert len(order_model.get_reserved()) == 1
```

### 예상 실패 이유

`ReserveController.__init__`이 인수 2개(order_model, view)만 받으므로
`ReserveController(order_model, sample_model, view)` → `TypeError`.

### 구현 방향

**`controllers/order_controller.py`:**
```python
class ReserveController:
    def __init__(self, order_model, sample_model, view) -> None:
        self._order = order_model
        self._sample = sample_model
        self._view = view

    def _handle_reserve(self) -> None:
        sample_id, customer_name, quantity = self._view.get_order_input()

        # 시료 존재 여부 검증
        if self._sample.get_by_id(sample_id) is None:
            self._view.show_error(f"시료 ID '{sample_id}'가 존재하지 않습니다.")
            return

        self._view.show_order_confirmation(sample_id, customer_name, quantity)
        yn = self._view.get_confirm_yn()
        if yn.upper() == "Y":
            order = self._order.reserve(sample_id, customer_name, quantity)
            self._view.show_reserve_success(order["order_no"], order["status"])
        else:
            self._view.show_reserve_cancelled()
```

**`app.py`:**
```python
reserve_ctrl = ReserveController(order_model, sample_model, order_view)
```

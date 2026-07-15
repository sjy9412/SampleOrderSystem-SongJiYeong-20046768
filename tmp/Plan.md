# TDD Plan — STEP 2: 시료 관리 View / Controller

## 목표 (Goal)

`SampleController`가 View에서 입력을 받아 `SampleModel`을 올바르게 조작하는지 검증한다.

- 메뉴 선택 `1` → `SampleModel.add()` 호출 → 시료 실제 저장됨
- 메뉴 선택 `2` → `SampleModel.get_all()` 결과를 `view.show_samples()`에 전달
- 메뉴 선택 `3` → `SampleModel.search()` 결과를 `view.show_samples()`에 전달
- 잘못된 선택 → `view.show_invalid_input()` 호출

---

## 작성할 테스트 (`tests/test_sample_controller.py`)

**전략:**
- View는 I/O 경계 → `MockSampleView`로 대체 (mock 허용)
- SampleModel은 실제 객체 사용, DB는 autouse 픽스처로 clean

```python
import pytest
from models.sample import SampleModel
from controllers.sample_controller import SampleController


class MockSampleView:
    def __init__(self):
        self.shown_samples = None
        self._choices = iter(['0'])
        self._sample_input = None
        self._keyword = None
        self.invalid_input_shown = False

    def show_menu(self): pass
    def get_menu_choice(self): return next(self._choices)
    def get_sample_input(self): return self._sample_input
    def get_search_keyword(self): return self._keyword
    def show_samples(self, samples, stocks): self.shown_samples = samples
    def show_error(self, msg): pass
    def show_invalid_input(self): self.invalid_input_shown = True
    def show_exit(self): pass
    def on_model_changed(self, event): pass
    def get_title_input(self): return ""
    def get_id_input(self, action): return ""


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("samples")
    yield
    store.reset("samples")


@pytest.fixture
def model():
    return SampleModel()


@pytest.fixture
def view():
    return MockSampleView()


def test_register_adds_sample_to_model(model, view):
    view._choices = iter(['1', '0'])
    view._sample_input = ("TestChip", 2.5, 0.9)
    SampleController(model, view).run()
    samples = model.get_all()
    assert len(samples) == 1
    assert samples[0]["name"] == "TestChip"
    assert samples[0]["avg_production_time"] == 2.5
    assert samples[0]["yield_rate"] == 0.9


def test_list_passes_all_samples_to_view(model, view):
    model.add("ChipA", 1.0, 0.8)
    model.add("ChipB", 2.0, 0.9)
    view._choices = iter(['2', '0'])
    SampleController(model, view).run()
    assert view.shown_samples is not None
    assert len(view.shown_samples) == 2


def test_search_passes_matching_samples_to_view(model, view):
    model.add("AlphaChip", 1.0, 0.8)
    model.add("BetaChip", 2.0, 0.9)
    view._choices = iter(['3', '0'])
    view._keyword = "Alpha"
    SampleController(model, view).run()
    assert view.shown_samples is not None
    assert len(view.shown_samples) == 1
    assert view.shown_samples[0]["name"] == "AlphaChip"


def test_invalid_choice_shows_invalid_input(model, view):
    view._choices = iter(['X', '0'])
    SampleController(model, view).run()
    assert view.invalid_input_shown is True
```

---

## 예상 실패 이유

`controllers/sample_controller.py`가 존재하지 않으므로 `ImportError`로 실패한다.

---

## 구현 방향 (GREEN 단계에서 작성할 최소 코드)

### `controllers/sample_controller.py`

```python
class SampleController:
    def __init__(self, model, view):
        self._model = model
        self._view = view

    def run(self):
        while True:
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == '0':
                break
            elif choice == '1':
                self._handle_register()
            elif choice == '2':
                self._handle_list()
            elif choice == '3':
                self._handle_search()
            else:
                self._view.show_invalid_input()

    def _handle_register(self):
        name, avg_time, yield_rate = self._view.get_sample_input()
        self._model.add(name, avg_time, yield_rate)

    def _handle_list(self):
        samples = self._model.get_all()
        self._view.show_samples(samples, {})

    def _handle_search(self):
        keyword = self._view.get_search_keyword()
        samples = self._model.search(keyword)
        self._view.show_samples(samples, {})
```

### `views/sample_view.py`

BaseView Protocol을 구현하며, 생성자에서 `model.subscribe(self)`로 Observer 등록한다.  
`show_samples(samples, stocks)`의 stocks는 STEP 4 전까지 빈 dict를 수신한다.

---

## 파일 목록

| 파일 | 역할 |
|------|------|
| `tests/test_sample_controller.py` | RED: 실패하는 테스트 |
| `controllers/sample_controller.py` | GREEN: Controller 구현 |
| `views/sample_view.py` | GREEN: View 구현 |

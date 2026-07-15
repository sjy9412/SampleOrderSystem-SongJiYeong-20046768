# TDD Plan — 시료 중복 등록 방지

## Goal

이름(`name`), 평균 생산 시간(`avg_production_time`), 수율(`yield_rate`) 세 가지가 모두 동일한 시료가 이미 존재하면 등록을 거부한다.

- **Model**: `SampleModel.add()`에서 `ValueError("이미 등록된 시료입니다.")` raise
- **Controller**: `_handle_register()`에서 `ValueError`를 catch하여 `view.show_error()` 호출

---

## 작성할 테스트

### 테스트 1 — Model: 중복 속성이면 ValueError (파일: `tests/test_sample_model.py`)

```python
def test_add_raises_when_duplicate_attributes(model):
    model.add("ChipX", 2.5, 0.95)
    with pytest.raises(ValueError, match="이미 등록된 시료입니다."):
        model.add("ChipX", 2.5, 0.95)
```

### 테스트 2 — Model: 속성 하나라도 다르면 정상 등록 (파일: `tests/test_sample_model.py`)

```python
def test_add_succeeds_when_only_name_differs(model):
    model.add("ChipX", 2.5, 0.95)
    result = model.add("ChipY", 2.5, 0.95)  # 이름만 다름
    assert result["name"] == "ChipY"
```

### 테스트 3 — Controller: 중복 시료 등록 시 show_error 호출 (파일: `tests/test_sample_controller.py`)

```python
def test_register_shows_error_on_duplicate(model, inventory_model, view):
    model.add("ChipX", 2.5, 0.95)

    view._choices = iter(['1', '0'])
    view._sample_input = ("ChipX", 2.5, 0.95)
    SampleController(model, inventory_model, view).run()

    assert view.last_error == "이미 등록된 시료입니다."
```

> `MockSampleView.show_error`가 `last_error`를 저장하도록 수정 필요.

---

## 예상 실패 이유

| 테스트 | 실패 원인 |
|--------|-----------|
| 테스트 1 | `SampleModel.add()`에 중복 체크 없음 → `ValueError` 미발생 |
| 테스트 2 | 테스트 1 수정 후 부작용 없음 확인용 (처음엔 통과할 수 있음) |
| 테스트 3 | `MockSampleView`에 `last_error` 없음 + `_handle_register`에 except 없음 |

---

## 구현 방향 (최소한의 변경)

### 1. `MockSampleView` 수정 (`tests/test_sample_controller.py`)

```python
def show_error(self, msg):
    self.last_error = msg
```

초기값 `self.last_error = None` 추가.

### 2. `SampleModel.add()` 수정 (`models/sample.py`)

```python
def add(self, name, avg_production_time, yield_rate):
    existing = [
        s for s in store.read_all(COLLECTION)
        if s["name"] == name
        and s["avg_production_time"] == avg_production_time
        and s["yield_rate"] == yield_rate
    ]
    if existing:
        raise ValueError("이미 등록된 시료입니다.")
    record = store.create(COLLECTION, {...})
    ...
```

### 3. `SampleController._handle_register()` 수정 (`controllers/sample_controller.py`)

```python
def _handle_register(self):
    name, avg_time, yield_rate = self._view.get_sample_input()
    try:
        self._model.add(name, avg_time, yield_rate)
    except ValueError as e:
        self._view.show_error(str(e))
```

---

## 영향 범위

| 파일 | 변경 내용 |
|------|-----------|
| `tests/test_sample_model.py` | 테스트 2개 추가 |
| `tests/test_sample_controller.py` | `MockSampleView` 수정, 테스트 1개 추가 |
| `models/sample.py` | `add()`에 중복 체크 로직 추가 |
| `controllers/sample_controller.py` | `_handle_register()`에 `try/except` 추가 |
| `docs/PRD.md` | 시료 중복 방지 규칙 명시 (완료) |

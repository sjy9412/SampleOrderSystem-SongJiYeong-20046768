# TDD Plan — SampleController 재고 연동

## Goal

`SampleController`가 시료 목록/검색 결과를 표시할 때, `stocks={}` 빈 딕트 대신
`InventoryModel`에서 조회한 실제 재고 수량을 `show_samples(samples, stocks)`에 전달한다.

---

## 작성할 테스트

**파일**: `tests/test_sample_controller.py`

### 테스트 1 — 목록 조회 시 실제 재고 전달

```python
def test_list_passes_stock_quantities_to_view(model, inventory_model, view):
    sample = model.add("ChipA", 1.0, 0.8)
    inventory_model.increase(sample["id"], 50)

    view._choices = iter(['2', '0'])
    SampleController(model, inventory_model, view).run()

    assert view.shown_stocks[sample["id"]] == 50
```

### 테스트 2 — 검색 시 실제 재고 전달

```python
def test_search_passes_stock_quantities_to_view(model, inventory_model, view):
    sample = model.add("AlphaChip", 1.0, 0.8)
    inventory_model.increase(sample["id"], 30)

    view._choices = iter(['3', '0'])
    view._keyword = "Alpha"
    SampleController(model, inventory_model, view).run()

    assert view.shown_stocks[sample["id"]] == 30
```

---

## 예상 실패 이유

- `SampleController.__init__`이 `inventory_model`을 인자로 받지 않으므로 `TypeError` 발생
- `MockSampleView.show_samples`가 `stocks`를 버리므로 `shown_stocks` 속성이 없어 `AttributeError` 발생

---

## 구현 방향 (최소한의 변경)

1. **`MockSampleView`** — `show_samples`에서 `stocks`도 저장하도록 수정
   (`self.shown_stocks = stocks`)

2. **`SampleController.__init__`** — `inventory_model` 파라미터 추가

3. **`_handle_list` / `_handle_search`** — `inventory_model.get_all_stocks()` 호출 후
   `{s["sample_id"]: s["quantity"] for s in ...}` 형태로 변환하여 전달

4. **`app.py`** — `SampleController(sample_model, inventory_model, SampleView(...))` 로 수정

---

## 영향 범위

| 파일 | 변경 내용 |
|------|-----------|
| `tests/test_sample_controller.py` | 픽스처 추가, 테스트 2개 추가, `MockSampleView` 수정 |
| `controllers/sample_controller.py` | `__init__` + `_handle_list` + `_handle_search` |
| `app.py` | `SampleController` 생성 시 `inventory_model` 전달 |

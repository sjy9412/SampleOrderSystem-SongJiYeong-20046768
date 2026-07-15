# TDD Plan — 시료 ID 순번 부여 (S-001, S-002, …)

## Goal

시료를 등록할 때 UUID 대신 `S-001`, `S-002`, … 형태의 순번 ID를 자동 부여한다.

- **기준**: 등록된 총 시료 수 + 1
- **형식**: `S-{n:03d}` (세 자리 제로패딩)
- **책임 위치**: `SampleModel.add()`에서 생성 후 `store.create()`에 전달
- `json_store.create()`는 변경 없음 — record 딕셔너리에 `id`를 포함하면 UUID보다 우선 적용되는 현재 구조 활용

---

## 작성할 테스트

### 테스트 1 — 첫 번째 시료의 ID는 S-001 (파일: `tests/test_sample_model.py`)

```python
def test_first_sample_gets_id_S001(model):
    sample = model.add("AlphaChip", 2.5, 0.95)
    assert sample["id"] == "S-001"
```

### 테스트 2 — 순서대로 S-001, S-002 부여 (파일: `tests/test_sample_model.py`)

```python
def test_samples_get_sequential_ids(model):
    s1 = model.add("AlphaChip", 2.5, 0.95)
    s2 = model.add("BetaChip", 1.0, 0.80)
    assert s1["id"] == "S-001"
    assert s2["id"] == "S-002"
```

### 테스트 3 — 기존 시료가 있어도 연속 번호 유지 (파일: `tests/test_sample_model.py`)

```python
def test_id_continues_from_existing_count(model):
    model.add("AlphaChip", 2.5, 0.95)   # S-001
    model.add("BetaChip", 1.0, 0.80)    # S-002
    s3 = model.add("GammaChip", 3.0, 0.90)
    assert s3["id"] == "S-003"
```

---

## 예상 실패 이유

| 테스트 | 실패 원인 |
|--------|-----------|
| 테스트 1 | `store.create()`가 UUID를 생성 → `"S-001"` 아님 |
| 테스트 2 | 동일 원인 |
| 테스트 3 | 동일 원인 |

---

## 구현 방향 (최소한의 변경)

### `SampleModel.add()` 수정 (`models/sample.py`)

```python
def add(self, name, avg_production_time, yield_rate):
    count = len(store.read_all(COLLECTION))
    next_id = f"S-{count + 1:03d}"
    record = store.create(COLLECTION, {
        "id": next_id,           # json_store가 **record로 UUID 덮어씀 방지
        "name": name,
        "avg_production_time": avg_production_time,
        "yield_rate": yield_rate,
    })
    self._notify(ModelEvent(type=EventType.ADDED, payload=record))
    return record
```

`json_store.create()` 내부:
```python
record = {
    "id": str(uuid.uuid4()),   # 기본값
    ...
    **record,                  # id가 포함되면 여기서 덮어씀 → S-001 적용됨
}
```

---

## 영향 범위

| 파일 | 변경 내용 |
|------|-----------|
| `tests/test_sample_model.py` | 테스트 3개 추가 |
| `models/sample.py` | `add()`에서 순번 ID 생성 후 전달 |
| `docs/PRD.md` | 시료 ID 형식 명시 (완료) |

기존 테스트 `test_add_returns_sample_with_id` — `sample["id"] is not None` 만 검증하므로 영향 없음.

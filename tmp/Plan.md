# TDD Plan — STEP 1: Sample 모델

## Goal

`models/sample.py`에 `SampleModel` 클래스를 구현한다.  
다음 네 가지 동작을 검증하는 테스트를 먼저 작성한다.

1. `add()` — 시료 등록 후 ADDED 이벤트 발행
2. `get_all()` — 전체 시료 목록 반환
3. `get_by_id()` — ID로 단건 조회 (없으면 None)
4. `search()` — 이름 기준 부분 문자열 검색

---

## 작성할 테스트 코드 (`tests/test_sample_model.py`)

```python
import pytest
from models.sample import SampleModel
from models.base import ModelEvent, EventType

# ── 픽스처 ────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clean_db():
    """각 테스트 전후로 samples 컬렉션을 초기화한다."""
    from db import json_store as store
    store.reset("samples")
    yield
    store.reset("samples")


@pytest.fixture
def model():
    return SampleModel()


# ── add ───────────────────────────────────────────────────────────────────────

def test_add_returns_sample_with_id(model):
    sample = model.add("AlphaChip", 2.5, 0.95)
    assert sample["id"] is not None
    assert sample["name"] == "AlphaChip"
    assert sample["avg_production_time"] == 2.5
    assert sample["yield_rate"] == 0.95


def test_add_emits_added_event(model):
    received = []

    class Observer:
        def on_model_changed(self, event: ModelEvent):
            received.append(event)

    model.subscribe(Observer())
    model.add("BetaChip", 1.0, 0.80)

    assert len(received) == 1
    assert received[0].type == EventType.ADDED
    assert received[0].payload["name"] == "BetaChip"


# ── get_all ───────────────────────────────────────────────────────────────────

def test_get_all_returns_empty_list_initially(model):
    assert model.get_all() == []


def test_get_all_returns_all_added_samples(model):
    model.add("AlphaChip", 2.5, 0.95)
    model.add("BetaChip", 1.0, 0.80)
    samples = model.get_all()
    assert len(samples) == 2
    names = {s["name"] for s in samples}
    assert names == {"AlphaChip", "BetaChip"}


# ── get_by_id ─────────────────────────────────────────────────────────────────

def test_get_by_id_returns_correct_sample(model):
    added = model.add("GammaChip", 3.0, 0.90)
    found = model.get_by_id(added["id"])
    assert found is not None
    assert found["name"] == "GammaChip"


def test_get_by_id_returns_none_for_unknown_id(model):
    assert model.get_by_id("nonexistent-id") is None


# ── search ────────────────────────────────────────────────────────────────────

def test_search_returns_matching_samples(model):
    model.add("AlphaChip", 2.5, 0.95)
    model.add("BetaChip", 1.0, 0.80)
    model.add("AlphaSensor", 1.5, 0.70)

    results = model.search("Alpha")
    assert len(results) == 2
    assert all("Alpha" in s["name"] for s in results)


def test_search_returns_empty_list_when_no_match(model):
    model.add("AlphaChip", 2.5, 0.95)
    assert model.search("Zeta") == []


def test_search_is_case_insensitive(model):
    model.add("AlphaChip", 2.5, 0.95)
    results = model.search("alpha")
    assert len(results) == 1
```

---

## 예상 실패 이유

- `models/sample.py`가 존재하지 않으므로 `ImportError`로 실패한다.
- `EventType`에 `LISTED`, `SEARCHED`가 없으므로 추가가 필요하다.

---

## 구현 방향 (최소한의 코드)

### 1. `models/base.py` — EventType 확장

```python
class EventType(Enum):
    ADDED    = auto()
    TOGGLED  = auto()
    DELETED  = auto()
    LISTED   = auto()   # 추가
    SEARCHED = auto()   # 추가
```

### 2. `models/sample.py` 신규 생성

```python
from __future__ import annotations
from models.base import ObservableModel, ModelEvent, EventType
from db import json_store as store

COLLECTION = "samples"

class SampleModel(ObservableModel):
    def add(self, name: str, avg_production_time: float, yield_rate: float) -> dict:
        record = store.create(COLLECTION, {
            "name": name,
            "avg_production_time": avg_production_time,
            "yield_rate": yield_rate,
        })
        self._notify(ModelEvent(type=EventType.ADDED, payload=record))
        return record

    def get_all(self) -> list[dict]:
        return store.read_all(COLLECTION)

    def get_by_id(self, sample_id: str) -> dict | None:
        return store.read_one(COLLECTION, sample_id)

    def search(self, keyword: str) -> list[dict]:
        keyword_lower = keyword.lower()
        return [s for s in store.read_all(COLLECTION)
                if keyword_lower in s["name"].lower()]
```

---

## 파일 변경 목록

| 파일 | 작업 |
|------|------|
| `models/base.py` | `EventType`에 `LISTED`, `SEARCHED` 추가 |
| `models/sample.py` | 신규 생성 |
| `tests/test_sample_model.py` | 신규 생성 (테스트 먼저) |
| `tests/__init__.py` | 신규 생성 (패키지 인식) |

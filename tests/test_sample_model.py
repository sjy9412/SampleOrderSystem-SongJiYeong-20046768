import pytest
from models.sample import SampleModel
from models.base import ModelEvent, EventType


@pytest.fixture(autouse=True)
def clean_db():
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

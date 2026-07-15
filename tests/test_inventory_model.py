import pytest
from models.inventory import InventoryModel


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("inventories")
    yield
    store.reset("inventories")


@pytest.fixture
def model():
    return InventoryModel()


# ── get_stock ─────────────────────────────────────────────────────────────────

def test_get_stock_returns_zero_for_unknown_sample(model):
    assert model.get_stock("nonexistent-sample") == 0


# ── increase ──────────────────────────────────────────────────────────────────

def test_increase_creates_stock_record(model):
    model.increase("sample-1", 50)
    assert model.get_stock("sample-1") == 50


def test_increase_accumulates_quantity(model):
    model.increase("sample-1", 30)
    model.increase("sample-1", 20)
    assert model.get_stock("sample-1") == 50


# ── decrease ──────────────────────────────────────────────────────────────────

def test_decrease_reduces_stock(model):
    model.increase("sample-1", 100)
    model.decrease("sample-1", 40)
    assert model.get_stock("sample-1") == 60


def test_decrease_raises_when_insufficient(model):
    model.increase("sample-1", 10)
    with pytest.raises(ValueError):
        model.decrease("sample-1", 20)


# ── is_sufficient ─────────────────────────────────────────────────────────────

def test_is_sufficient_returns_true_when_enough(model):
    model.increase("sample-1", 100)
    assert model.is_sufficient("sample-1", 100) is True


def test_is_sufficient_returns_false_when_not_enough(model):
    model.increase("sample-1", 5)
    assert model.is_sufficient("sample-1", 10) is False


# ── get_all_stocks ────────────────────────────────────────────────────────────

def test_get_all_stocks_returns_all_records(model):
    model.increase("sample-1", 10)
    model.increase("sample-2", 20)
    model.increase("sample-3", 30)
    stocks = model.get_all_stocks()
    assert len(stocks) == 3


# ── get_status ────────────────────────────────────────────────────────────────

def test_get_status_returns_여유_when_sufficient(model):
    model.increase("sample-1", 100)
    assert model.get_status("sample-1", 100) == "여유"


def test_get_status_returns_부족_when_low(model):
    model.increase("sample-1", 5)
    assert model.get_status("sample-1", 10) == "부족"


def test_get_status_returns_고갈_when_zero(model):
    assert model.get_status("sample-1", 10) == "고갈"

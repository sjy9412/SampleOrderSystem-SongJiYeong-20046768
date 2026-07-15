import re
import pytest
from models.order import OrderModel
from models.base import ModelEvent, EventType


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("orders")
    yield
    store.reset("orders")


@pytest.fixture
def model():
    return OrderModel()


# ── reserve ───────────────────────────────────────────────────────────────────

def test_reserve_returns_order_with_id(model):
    order = model.reserve("sample-1", "홍길동", 10)
    assert order["id"] is not None
    assert order["sample_id"] == "sample-1"
    assert order["customer_name"] == "홍길동"
    assert order["quantity"] == 10
    assert order["status"] == "RESERVED"


def test_reserve_emits_added_event(model):
    received = []

    class Observer:
        def on_model_changed(self, event: ModelEvent):
            received.append(event)

    model.subscribe(Observer())
    model.reserve("sample-1", "홍길동", 10)

    assert len(received) == 1
    assert received[0].type == EventType.ADDED
    assert received[0].payload["customer_name"] == "홍길동"


# ── get_reserved ──────────────────────────────────────────────────────────────

def test_get_reserved_returns_only_reserved_orders(model):
    model.reserve("sample-1", "홍길동", 10)
    order2 = model.reserve("sample-2", "이순신", 5)
    model.confirm(order2["id"])

    reserved = model.get_reserved()
    assert len(reserved) == 1
    assert reserved[0]["customer_name"] == "홍길동"


# ── get_by_status ─────────────────────────────────────────────────────────────

def test_get_by_status_returns_matching_orders(model):
    o1 = model.reserve("sample-1", "홍길동", 10)
    o2 = model.reserve("sample-2", "이순신", 5)
    model.confirm(o1["id"])
    model.reject(o2["id"])

    confirmed = model.get_by_status("CONFIRMED")
    assert len(confirmed) == 1
    assert confirmed[0]["customer_name"] == "홍길동"

    rejected = model.get_by_status("REJECTED")
    assert len(rejected) == 1
    assert rejected[0]["customer_name"] == "이순신"


# ── get_by_id ─────────────────────────────────────────────────────────────────

def test_get_by_id_returns_correct_order(model):
    added = model.reserve("sample-1", "홍길동", 10)
    found = model.get_by_id(added["id"])
    assert found is not None
    assert found["customer_name"] == "홍길동"


def test_get_by_id_returns_none_for_unknown_id(model):
    assert model.get_by_id("nonexistent-id") is None


# ── confirm ───────────────────────────────────────────────────────────────────

def test_confirm_changes_status_to_confirmed(model):
    order = model.reserve("sample-1", "홍길동", 10)
    model.confirm(order["id"])
    updated = model.get_by_id(order["id"])
    assert updated["status"] == "CONFIRMED"


def test_confirm_only_works_on_reserved_order(model):
    order = model.reserve("sample-1", "홍길동", 10)
    model.set_producing(order["id"])
    with pytest.raises(ValueError):
        model.confirm(order["id"])


# ── reject ────────────────────────────────────────────────────────────────────

def test_reject_changes_status_to_rejected(model):
    order = model.reserve("sample-1", "홍길동", 10)
    model.reject(order["id"])
    updated = model.get_by_id(order["id"])
    assert updated["status"] == "REJECTED"


def test_reject_only_works_on_reserved_order(model):
    order = model.reserve("sample-1", "홍길동", 10)
    model.confirm(order["id"])
    with pytest.raises(ValueError):
        model.reject(order["id"])


# ── set_producing ─────────────────────────────────────────────────────────────

def test_set_producing_changes_status_to_producing(model):
    order = model.reserve("sample-1", "홍길동", 10)
    model.set_producing(order["id"])
    updated = model.get_by_id(order["id"])
    assert updated["status"] == "PRODUCING"


def test_set_producing_only_works_on_reserved_order(model):
    order = model.reserve("sample-1", "홍길동", 10)
    model.confirm(order["id"])
    with pytest.raises(ValueError):
        model.set_producing(order["id"])


# ── release ───────────────────────────────────────────────────────────────────

def test_release_changes_status_to_release(model):
    order = model.reserve("sample-1", "홍길동", 10)
    model.confirm(order["id"])
    model.release(order["id"])
    updated = model.get_by_id(order["id"])
    assert updated["status"] == "RELEASE"


def test_release_only_works_on_confirmed_order(model):
    order = model.reserve("sample-1", "홍길동", 10)
    with pytest.raises(ValueError):
        model.release(order["id"])


# ── order_no 생성 ─────────────────────────────────────────────────────────────

def test_reserve_generates_order_no_with_format(model):
    order = model.reserve("sample-1", "홍길동", 10)
    assert re.match(r"ORD-\d{8}-\d{4}", order["order_no"])


def test_reserve_sequential_order_no_on_same_day(model):
    o1 = model.reserve("sample-1", "홍길동", 5)
    o2 = model.reserve("sample-2", "이순신", 3)
    seq1 = int(o1["order_no"].split("-")[2])
    seq2 = int(o2["order_no"].split("-")[2])
    assert seq2 == seq1 + 1

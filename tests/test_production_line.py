import pytest
from models.production_line import ProductionLine
from models.order import OrderModel
from models.inventory import InventoryModel
from models.sample import SampleModel


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("production_queue")
    store.reset("orders")
    store.reset("inventories")
    store.reset("samples")
    yield
    store.reset("production_queue")
    store.reset("orders")
    store.reset("inventories")
    store.reset("samples")


@pytest.fixture
def order_model():
    return OrderModel()


@pytest.fixture
def inventory_model():
    return InventoryModel()


@pytest.fixture
def sample_model():
    return SampleModel()


@pytest.fixture
def production_line(order_model, inventory_model, sample_model):
    return ProductionLine(order_model, inventory_model, sample_model)


# ── calculate_production ──────────────────────────────────────────────────────

def test_calculate_production_returns_correct_values(production_line):
    actual_qty, total_time = production_line.calculate_production(
        shortage=90, yield_rate=0.9, avg_time=2.0
    )
    assert actual_qty == 100
    assert total_time == 200.0


def test_calculate_production_uses_ceil(production_line):
    actual_qty, _ = production_line.calculate_production(
        shortage=10, yield_rate=0.3, avg_time=1.0
    )
    assert actual_qty == 34  # ceil(10 / 0.3) = ceil(33.33...) = 34


# ── enqueue / get_queue / get_current ─────────────────────────────────────────

def test_enqueue_adds_order_to_queue(production_line):
    production_line.enqueue("order-1")
    queue = production_line.get_queue()
    assert len(queue) == 1
    assert queue[0]["order_id"] == "order-1"


def test_get_queue_returns_orders_in_fifo_order(production_line):
    production_line.enqueue("order-1")
    production_line.enqueue("order-2")
    queue = production_line.get_queue()
    assert queue[0]["order_id"] == "order-1"
    assert queue[1]["order_id"] == "order-2"


def test_get_current_returns_first_in_queue(production_line):
    production_line.enqueue("order-1")
    production_line.enqueue("order-2")
    current = production_line.get_current()
    assert current["order_id"] == "order-1"


def test_get_current_returns_none_when_queue_is_empty(production_line):
    assert production_line.get_current() is None


# ── complete ──────────────────────────────────────────────────────────────────

def test_complete_increases_inventory(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료A", avg_production_time=2.0, yield_rate=0.5)
    inventory_model.increase(sample["id"], 5)
    order = order_model.reserve(sample["id"], "홍길동", 15)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    production_line.complete(order["id"])

    # shortage=10, yield=0.5 → actual_qty=20
    assert inventory_model.get_stock(sample["id"]) == 5 + 20


def test_complete_confirms_order(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료B", avg_production_time=1.0, yield_rate=1.0)
    inventory_model.increase(sample["id"], 0)
    order = order_model.reserve(sample["id"], "이순신", 10)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    production_line.complete(order["id"])

    updated = order_model.get_by_id(order["id"])
    assert updated["status"] == "CONFIRMED"


def test_complete_removes_order_from_queue(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료C", avg_production_time=1.0, yield_rate=1.0)
    order = order_model.reserve(sample["id"], "강감찬", 5)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    production_line.complete(order["id"])

    assert production_line.get_queue() == []

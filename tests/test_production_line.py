import pytest
from datetime import datetime, timezone, timedelta
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


# ── get_current_info 확장 ────────────────────────────────────────────────────

def test_get_current_info_includes_stock_and_shortage(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료D", avg_production_time=2.0, yield_rate=0.8)
    inventory_model.increase(sample["id"], 30)
    order = order_model.reserve(sample["id"], "테스트", 50)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    info = production_line.get_current_info()

    assert info["stock"] == 30
    assert info["shortage"] == 20  # 50 - 30


def test_get_current_info_includes_yield_rate_and_avg_time(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료E", avg_production_time=1.5, yield_rate=0.75)
    inventory_model.increase(sample["id"], 0)
    order = order_model.reserve(sample["id"], "테스트", 10)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    info = production_line.get_current_info()

    assert info["yield_rate"] == pytest.approx(0.75)
    assert info["avg_time"] == pytest.approx(1.5)


def test_get_current_info_includes_order_no(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료F", avg_production_time=1.0, yield_rate=1.0)
    inventory_model.increase(sample["id"], 0)
    order = order_model.reserve(sample["id"], "테스트", 5)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    info = production_line.get_current_info()

    assert "order_no" in info
    assert info["order_no"].startswith("ORD-")


def test_get_current_info_calculates_progress_pct(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료G", avg_production_time=2.0, yield_rate=1.0)
    inventory_model.increase(sample["id"], 0)
    order = order_model.reserve(sample["id"], "테스트", 10)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    # total_time = 2.0 × 10 = 20분, now = created_at + 10분 → 50%
    queue_item = production_line.get_current()
    created_at = datetime.fromisoformat(queue_item["created_at"])
    fake_now = created_at + timedelta(minutes=10)

    info = production_line.get_current_info(now=fake_now)

    assert info["progress_pct"] == pytest.approx(50.0)


def test_get_current_info_includes_estimated_completion(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료H", avg_production_time=1.0, yield_rate=1.0)
    inventory_model.increase(sample["id"], 0)
    order = order_model.reserve(sample["id"], "테스트", 5)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    info = production_line.get_current_info()

    assert "estimated_completion" in info
    assert isinstance(info["estimated_completion"], str)
    assert len(info["estimated_completion"]) > 0


# ── get_queue_info 확장 ──────────────────────────────────────────────────────

def test_get_queue_info_excludes_currently_producing_order(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료I", avg_production_time=1.0, yield_rate=1.0)
    inventory_model.increase(sample["id"], 0)
    order_current = order_model.reserve(sample["id"], "생산중", 5)
    order_waiting = order_model.reserve(sample["id"], "대기중", 3)
    order_model.set_producing(order_current["id"])
    order_model.set_producing(order_waiting["id"])
    production_line.enqueue(order_current["id"])
    production_line.enqueue(order_waiting["id"])

    queue_info = production_line.get_queue_info()

    assert len(queue_info) == 1
    assert queue_info[0]["order_no"] == order_waiting["order_no"]


def test_get_queue_info_includes_order_no(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료J", avg_production_time=1.0, yield_rate=1.0)
    inventory_model.increase(sample["id"], 0)
    order_current = order_model.reserve(sample["id"], "생산중", 5)
    order_waiting = order_model.reserve(sample["id"], "대기중", 3)
    order_model.set_producing(order_current["id"])
    order_model.set_producing(order_waiting["id"])
    production_line.enqueue(order_current["id"])
    production_line.enqueue(order_waiting["id"])

    queue_info = production_line.get_queue_info()

    assert queue_info[0]["order_no"] == order_waiting["order_no"]


def test_get_queue_info_includes_shortage_and_actual_qty(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료K", avg_production_time=2.0, yield_rate=0.5)
    inventory_model.increase(sample["id"], 5)
    order_current = order_model.reserve(sample["id"], "생산중", 5)
    order_waiting = order_model.reserve(sample["id"], "대기중", 15)
    order_model.set_producing(order_current["id"])
    order_model.set_producing(order_waiting["id"])
    production_line.enqueue(order_current["id"])
    production_line.enqueue(order_waiting["id"])

    queue_info = production_line.get_queue_info()

    assert queue_info[0]["shortage"] == 10        # 15 - 5
    assert queue_info[0]["actual_qty"] == 20      # ceil(10 / 0.5)


def test_get_queue_info_cumulative_estimated_completion(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료L", avg_production_time=2.0, yield_rate=1.0)
    inventory_model.increase(sample["id"], 0)
    order_current = order_model.reserve(sample["id"], "생산중", 5)   # total_time=10min
    order_wait1 = order_model.reserve(sample["id"], "대기1", 10)     # total_time=20min
    order_wait2 = order_model.reserve(sample["id"], "대기2", 5)      # total_time=10min
    order_model.set_producing(order_current["id"])
    order_model.set_producing(order_wait1["id"])
    order_model.set_producing(order_wait2["id"])
    production_line.enqueue(order_current["id"])
    production_line.enqueue(order_wait1["id"])
    production_line.enqueue(order_wait2["id"])

    queue_info = production_line.get_queue_info()

    assert len(queue_info) == 2
    assert queue_info[1]["estimated_completion"] > queue_info[0]["estimated_completion"]

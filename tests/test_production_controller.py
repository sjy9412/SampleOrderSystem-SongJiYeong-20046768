import pytest
from models.sample import SampleModel
from models.order import OrderModel
from models.inventory import InventoryModel
from models.production_line import ProductionLine
from controllers.production_controller import ProductionController


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("samples")
    store.reset("orders")
    store.reset("inventories")
    store.reset("production_queue")
    yield
    store.reset("samples")
    store.reset("orders")
    store.reset("inventories")
    store.reset("production_queue")


class ProductionViewStub:
    def __init__(self, model):
        model.subscribe(self)
        self._inputs = iter([])
        self.shown_current = None
        self.no_current_shown = False
        self.shown_queue = []

    def set_inputs(self, *values):
        self._inputs = iter(values)

    def _next(self):
        return next(self._inputs)

    def show_menu(self): pass
    def get_menu_choice(self): return self._next()
    def show_current(self, info): self.shown_current = info
    def show_no_current(self): self.no_current_shown = True
    def show_queue(self, items): self.shown_queue = list(items)
    def show_error(self, message): pass
    def show_invalid_input(self): pass
    def show_exit(self): pass
    def get_title_input(self): return ""
    def get_id_input(self, action): return ""
    def on_model_changed(self, event): pass


@pytest.fixture
def sample_model():
    return SampleModel()


@pytest.fixture
def order_model():
    return OrderModel()


@pytest.fixture
def inventory_model():
    return InventoryModel()


@pytest.fixture
def production_line(order_model, inventory_model, sample_model):
    return ProductionLine(order_model, inventory_model, sample_model)


@pytest.fixture
def view(production_line):
    return ProductionViewStub(production_line)


@pytest.fixture
def controller(production_line, view):
    return ProductionController(production_line, view)


# ── TC-1: 현재 생산 중인 주문 있을 때 현황 조회 ───────────────────────────────

def test_current_shows_production_info(
    controller, production_line, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("AAA", 2.0, 0.8)
    inventory_model.increase(sample["id"], 3)
    order = order_model.reserve(sample["id"], "홍길동", 10)
    order_model.set_producing(order["id"])
    production_line.enqueue(order["id"])

    view.set_inputs("1", "0")
    controller.run()

    # 부족분=7, 실생산량=ceil(7/0.8)=9, 총시간=2.0×9=18.0
    assert view.shown_current["order_id"] == order["id"]
    assert view.shown_current["sample_name"] == "AAA"
    assert view.shown_current["quantity"] == 10
    assert view.shown_current["actual_qty"] == 9
    assert view.shown_current["total_time"] == 18.0


# ── TC-2: 큐가 비어있을 때 현황 조회 ──────────────────────────────────────────

def test_current_when_empty_shows_no_current(controller, view):
    view.set_inputs("1", "0")
    controller.run()

    assert view.shown_current is None
    assert view.no_current_shown is True


# ── TC-3: 대기 주문 목록 조회 ─────────────────────────────────────────────────

def test_queue_shows_waiting_orders_in_order(
    controller, production_line, order_model, sample_model, view
):
    sample = sample_model.add("AAA", 2.0, 0.8)
    order1 = order_model.reserve(sample["id"], "홍길동", 5)
    order2 = order_model.reserve(sample["id"], "이순신", 3)
    order_model.set_producing(order1["id"])
    order_model.set_producing(order2["id"])
    production_line.enqueue(order1["id"])
    production_line.enqueue(order2["id"])

    view.set_inputs("2", "0")
    controller.run()

    assert len(view.shown_queue) == 2
    assert view.shown_queue[0]["position"] == 1
    assert view.shown_queue[0]["order_no"] == order1["order_no"]
    assert view.shown_queue[0]["sample_name"] == "AAA"
    assert view.shown_queue[0]["customer_name"] == "홍길동"
    assert view.shown_queue[1]["position"] == 2
    assert view.shown_queue[1]["customer_name"] == "이순신"

import pytest
from models.order import OrderModel
from models.inventory import InventoryModel
from controllers.order_controller import ReserveController
from controllers.approve_reject_controller import ApproveRejectController


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("orders")
    store.reset("inventories")
    yield
    store.reset("orders")
    store.reset("inventories")


class ProductionLineStub:
    def __init__(self):
        self.enqueued = []

    def enqueue(self, order_id: str) -> None:
        self.enqueued.append(order_id)


class OrderViewStub:
    def __init__(self, model):
        model.subscribe(self)
        self._inputs = iter([])
        self.shown_orders = []
        self.stock_insufficient_shown = False

    def set_inputs(self, *values):
        self._inputs = iter(values)

    def _next(self):
        return next(self._inputs)

    def show_menu(self): pass
    def show_reserve_menu(self): pass
    def show_approve_reject_menu(self): pass
    def get_menu_choice(self): return self._next()
    def get_order_input(self): return self._next()
    def get_order_id(self, action): return self._next()
    def get_approve_or_reject(self): return self._next()
    def show_orders(self, orders): self.shown_orders = list(orders)
    def show_stock_insufficient(self, stock, required): self.stock_insufficient_shown = True
    def show_error(self, message): pass
    def show_invalid_input(self): pass
    def show_exit(self): pass
    def get_title_input(self): return ""
    def get_id_input(self, action): return ""
    def on_model_changed(self, event): pass


@pytest.fixture
def order_model():
    return OrderModel()


@pytest.fixture
def inventory_model():
    return InventoryModel()


@pytest.fixture
def production_line():
    return ProductionLineStub()


@pytest.fixture
def view(order_model):
    return OrderViewStub(order_model)


@pytest.fixture
def reserve_ctrl(order_model, view):
    return ReserveController(order_model, view)


@pytest.fixture
def approve_reject_ctrl(order_model, inventory_model, production_line, view):
    return ApproveRejectController(order_model, inventory_model, production_line, view)


# ── TC-1: 주문 접수 → RESERVED 주문 생성 ──────────────────────────────────────

def test_reserve_creates_reserved_order(reserve_ctrl, order_model, view):
    view.set_inputs("1", ("sample-1", "홍길동", 5), "0")
    reserve_ctrl.run()

    orders = order_model.get_reserved()
    assert len(orders) == 1
    assert orders[0]["sample_id"] == "sample-1"
    assert orders[0]["customer_name"] == "홍길동"
    assert orders[0]["quantity"] == 5
    assert orders[0]["status"] == "RESERVED"


# ── TC-2: 승인/거절 메뉴 진입 시 RESERVED 목록 표시 ──────────────────────────

def test_approve_reject_menu_shows_reserved_orders(approve_reject_ctrl, order_model, view):
    order_model.reserve("sample-1", "홍길동", 5)
    order_model.reserve("sample-2", "이순신", 3)

    view.set_inputs("1", "", "0")
    approve_reject_ctrl.run()

    assert len(view.shown_orders) == 2
    assert all(o["status"] == "RESERVED" for o in view.shown_orders)


# ── TC-3: 승인 + 재고 충분 → CONFIRMED + 재고 차감 ───────────────────────────

def test_approve_confirms_when_stock_sufficient(
    approve_reject_ctrl, order_model, inventory_model, view
):
    inventory_model.increase("sample-1", 10)
    order = order_model.reserve("sample-1", "홍길동", 5)

    view.set_inputs("1", order["id"], "승인", "0")
    approve_reject_ctrl.run()

    updated = order_model.get_by_id(order["id"])
    assert updated["status"] == "CONFIRMED"
    assert inventory_model.get_stock("sample-1") == 5


# ── TC-4: 승인 + 재고 부족 + 재확인 승인 → PRODUCING + enqueue ───────────────

def test_approve_sets_producing_when_stock_insufficient_and_reconfirmed(
    approve_reject_ctrl, order_model, inventory_model, production_line, view
):
    inventory_model.increase("sample-1", 2)
    order = order_model.reserve("sample-1", "홍길동", 5)

    view.set_inputs("1", order["id"], "승인", "승인", "0")
    approve_reject_ctrl.run()

    updated = order_model.get_by_id(order["id"])
    assert updated["status"] == "PRODUCING"
    assert order["id"] in production_line.enqueued
    assert view.stock_insufficient_shown is True


# ── TC-5: 승인 + 재고 부족 + 재확인 거절 → REJECTED ──────────────────────────

def test_approve_insufficient_stock_then_reject_sets_rejected(
    approve_reject_ctrl, order_model, inventory_model, view
):
    inventory_model.increase("sample-1", 2)
    order = order_model.reserve("sample-1", "홍길동", 5)

    view.set_inputs("1", order["id"], "승인", "거절", "0")
    approve_reject_ctrl.run()

    updated = order_model.get_by_id(order["id"])
    assert updated["status"] == "REJECTED"
    assert view.stock_insufficient_shown is True


# ── TC-6: 거절 → REJECTED ─────────────────────────────────────────────────────

def test_reject_sets_rejected(approve_reject_ctrl, order_model, view):
    order = order_model.reserve("sample-1", "홍길동", 5)

    view.set_inputs("1", order["id"], "거절", "0")
    approve_reject_ctrl.run()

    updated = order_model.get_by_id(order["id"])
    assert updated["status"] == "REJECTED"

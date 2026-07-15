import pytest
from models.order import OrderModel
from controllers.release_controller import ReleaseController


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("orders")
    yield
    store.reset("orders")


class ReleaseViewStub:
    def __init__(self, model):
        model.subscribe(self)
        self._inputs = iter([])
        self.shown_orders = []
        self.errors = []

    def set_inputs(self, *values):
        self._inputs = iter(values)

    def _next(self):
        return next(self._inputs)

    def show_menu(self): pass
    def get_menu_choice(self): return self._next()
    def get_order_id(self, action): return self._next()
    def show_orders(self, orders): self.shown_orders = list(orders)
    def show_error(self, message): self.errors.append(message)
    def show_invalid_input(self): pass
    def show_exit(self): pass
    def get_title_input(self): return ""
    def get_id_input(self, action): return ""
    def on_model_changed(self, event): pass


@pytest.fixture
def order_model():
    return OrderModel()


@pytest.fixture
def view(order_model):
    return ReleaseViewStub(order_model)


@pytest.fixture
def controller(order_model, view):
    return ReleaseController(order_model, view)


# ── TC-1: 메뉴 1 → CONFIRMED 주문만 목록 표시 ────────────────────────────────

def test_list_confirmed_orders_shows_only_confirmed(controller, order_model, view):
    order1 = order_model.reserve("sample-1", "홍길동", 5)
    order_model.confirm(order1["id"])
    order2 = order_model.reserve("sample-2", "이순신", 3)
    order_model.confirm(order2["id"])
    order_model.reserve("sample-3", "강감찬", 2)  # RESERVED — 표시 안 됨

    view.set_inputs("1", "0")
    controller.run()

    assert len(view.shown_orders) == 2
    assert all(o["status"] == "CONFIRMED" for o in view.shown_orders)


# ── TC-2: 메뉴 2 → order_id 입력 → CONFIRMED → RELEASE ──────────────────────

def test_release_transitions_confirmed_order_to_release(controller, order_model, view):
    order = order_model.reserve("sample-1", "홍길동", 5)
    order_model.confirm(order["id"])

    view.set_inputs("2", order["id"], "0")
    controller.run()

    updated = order_model.get_by_id(order["id"])
    assert updated["status"] == "RELEASE"


# ── TC-3: CONFIRMED 아닌 주문 출고 시도 → 오류 표시 ──────────────────────────

def test_release_non_confirmed_order_shows_error(controller, order_model, view):
    order = order_model.reserve("sample-1", "홍길동", 5)  # RESERVED 상태

    view.set_inputs("2", order["id"], "0")
    controller.run()

    assert len(view.errors) == 1

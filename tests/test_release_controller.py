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
        self.release_result = None
        self.errors = []

    def set_inputs(self, *values):
        self._inputs = iter(values)

    def _next(self):
        return next(self._inputs)

    def show_confirmed_orders(self, orders):
        self.shown_orders = list(orders)

    def get_release_number(self, count):
        return self._next()

    def show_release_result(self, order):
        self.release_result = order

    def show_error(self, message):
        self.errors.append(message)

    def on_model_changed(self, event):
        pass


@pytest.fixture
def order_model():
    return OrderModel()


@pytest.fixture
def view(order_model):
    return ReleaseViewStub(order_model)


@pytest.fixture
def controller(order_model, view):
    return ReleaseController(order_model, view)


# ── TC-1: 진입 시 CONFIRMED 주문 목록 자동 표시 ─────────────────────────────────

def test_shows_confirmed_orders_immediately_on_entry(controller, order_model, view):
    order = order_model.reserve("S-001", "홍길동", 5)
    order_model.confirm(order["id"])

    view.set_inputs("0")
    controller.run()

    assert len(view.shown_orders) == 1
    assert view.shown_orders[0]["status"] == "CONFIRMED"


# ── TC-2: CONFIRMED 주문 없으면 목록 표시 후 바로 복귀 ──────────────────────────

def test_no_confirmed_orders_returns_without_prompting(controller, order_model, view):
    order_model.reserve("S-001", "홍길동", 5)  # RESERVED 상태

    controller.run()

    assert view.shown_orders == []
    assert view.release_result is None


# ── TC-3: 번호 입력으로 RELEASE 전환 ────────────────────────────────────────────

def test_release_by_number_transitions_to_release(controller, order_model, view):
    order = order_model.reserve("S-001", "홍길동", 5)
    order_model.confirm(order["id"])

    view.set_inputs("1")
    controller.run()

    updated = order_model.get_by_id(order["id"])
    assert updated["status"] == "RELEASE"


# ── TC-4: 출고 완료 후 결과 표시 ────────────────────────────────────────────────

def test_shows_release_result_after_processing(controller, order_model, view):
    order = order_model.reserve("S-001", "홍길동", 5)
    order_model.confirm(order["id"])

    view.set_inputs("1")
    controller.run()

    assert view.release_result is not None
    assert view.release_result["status"] == "RELEASE"


# ── TC-5: 유효하지 않은 번호 입력 시 오류 표시 ──────────────────────────────────

def test_invalid_number_shows_error(controller, order_model, view):
    order = order_model.reserve("S-001", "홍길동", 5)
    order_model.confirm(order["id"])

    view.set_inputs("99")
    controller.run()

    assert len(view.errors) == 1
    assert view.release_result is None

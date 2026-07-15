import re
import pytest
from models.order import OrderModel
from models.sample import SampleModel
from models.inventory import InventoryModel
from controllers.order_controller import ReserveController
from controllers.approve_reject_controller import ApproveRejectController


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("orders")
    store.reset("inventories")
    store.reset("samples")
    yield
    store.reset("orders")
    store.reset("inventories")
    store.reset("samples")


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
        self.shown_reserved_numbered = []
        self.stock_insufficient_shown = False
        self.stock_checking_name = None
        self.stock_detail_params = None
        self.approve_result = None
        self.confirmation_shown = False
        self.last_order_no = None
        self.last_status = None
        self.cancelled = False
        self.last_error = None

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
    def show_reserved_orders_numbered(self, orders):
        self.shown_reserved_numbered = list(orders)
    def get_order_number_choice(self, count): return self._next()
    def show_stock_checking(self, sample_name):
        self.stock_checking_name = sample_name
    def show_stock_detail(self, sample_name, stock, quantity, shortage):
        self.stock_detail_params = dict(
            sample_name=sample_name, stock=stock, quantity=quantity, shortage=shortage
        )
    def show_approve_result(self, order_no, status):
        self.approve_result = (order_no, status)
    def show_stock_insufficient(self, stock, required): self.stock_insufficient_shown = True
    def show_error(self, message):
        self.last_error = message
    def show_invalid_input(self): pass
    def show_exit(self): pass
    def get_title_input(self): return ""
    def get_id_input(self, action): return ""
    def on_model_changed(self, event): pass
    def show_order_confirmation(self, sample_id, customer_name, quantity):
        self.confirmation_shown = True
    def get_confirm_yn(self): return self._next()
    def show_reserve_success(self, order_no, status):
        self.last_order_no = order_no
        self.last_status = status
    def show_reserve_cancelled(self): self.cancelled = True


@pytest.fixture
def order_model():
    return OrderModel()


@pytest.fixture
def sample_model():
    return SampleModel()


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
def reserve_ctrl(order_model, sample_model, view):
    return ReserveController(order_model, sample_model, view)


@pytest.fixture
def approve_reject_ctrl(order_model, sample_model, inventory_model, production_line, view):
    return ApproveRejectController(order_model, sample_model, inventory_model, production_line, view)


# ── TC-1: 주문 접수 → RESERVED 주문 생성 ──────────────────────────────────────

def test_reserve_creates_reserved_order(reserve_ctrl, order_model, sample_model, view):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    view.set_inputs((sample["id"], "홍길동", 5), "Y")
    reserve_ctrl.run()

    orders = order_model.get_reserved()
    assert len(orders) == 1
    assert orders[0]["sample_id"] == sample["id"]
    assert orders[0]["customer_name"] == "홍길동"
    assert orders[0]["quantity"] == 5
    assert orders[0]["status"] == "RESERVED"


# ── TC-7: 확인 패널이 표시된다 ───────────────────────────────────────────────

def test_reserve_shows_confirmation_before_reserving(reserve_ctrl, sample_model, view):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    view.set_inputs((sample["id"], "홍길동", 5), "Y")
    reserve_ctrl.run()
    assert view.confirmation_shown is True


# ── TC-8: N 선택 시 주문이 생성되지 않는다 ──────────────────────────────────

def test_reserve_cancels_on_n(reserve_ctrl, order_model, sample_model, view):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    view.set_inputs((sample["id"], "홍길동", 5), "N")
    reserve_ctrl.run()
    assert len(order_model.get_reserved()) == 0
    assert view.cancelled is True


# ── TC-9: Y 선택 시 order_no와 상태가 뷰에 전달된다 ─────────────────────────

def test_reserve_shows_order_no_and_status_on_success(reserve_ctrl, sample_model, view):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    view.set_inputs((sample["id"], "홍길동", 5), "Y")
    reserve_ctrl.run()
    assert view.last_order_no is not None
    assert re.match(r"ORD-\d{8}-\d{4}", view.last_order_no)
    assert view.last_status == "RESERVED"


# ── TC-10: 존재하지 않는 시료 ID → 주문 미생성 + 에러 표시 ─────────────────

def test_reserve_shows_error_for_nonexistent_sample(reserve_ctrl, order_model, view):
    view.set_inputs(("S-999", "홍길동", 5), "Y")
    reserve_ctrl.run()
    assert len(order_model.get_reserved()) == 0
    assert view.last_error is not None
    assert "시료" in view.last_error


# ── TC-AR-1: 진입 시 RESERVED 목록 즉시 표시 (서브메뉴 없음) ─────────────────

def test_run_immediately_shows_reserved_orders(
    approve_reject_ctrl, order_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    order_model.reserve(sample["id"], "홍길동", 5)
    order_model.reserve(sample["id"], "이순신", 3)
    view.set_inputs(0)
    approve_reject_ctrl.run()
    assert len(view.shown_reserved_numbered) == 2
    assert all(o["status"] == "RESERVED" for o in view.shown_reserved_numbered)


# ── TC-AR-2: 재고 충분 → 즉시 CONFIRMED + 재고 차감 ─────────────────────────

def test_approve_confirms_when_stock_sufficient(
    approve_reject_ctrl, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 10)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, 0)
    approve_reject_ctrl.run()
    assert order_model.get_by_id(order["id"])["status"] == "CONFIRMED"
    assert inventory_model.get_stock(sample["id"]) == 5


# ── TC-AR-3: 재고 충분 → show_stock_checking, show_stock_detail 호출됨 ────────

def test_approve_sufficient_shows_stock_info(
    approve_reject_ctrl, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 10)
    order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, 0)
    approve_reject_ctrl.run()
    assert view.stock_checking_name == "실리콘 웨이퍼"
    assert view.stock_detail_params["shortage"] == 0


# ── TC-AR-4: 재고 부족 + 재확인 승인 → PRODUCING + enqueue ──────────────────

def test_approve_sets_producing_when_stock_insufficient_and_reconfirmed(
    approve_reject_ctrl, order_model, inventory_model, production_line, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 2)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, "승인", 0)
    approve_reject_ctrl.run()
    assert order_model.get_by_id(order["id"])["status"] == "PRODUCING"
    assert order["id"] in production_line.enqueued


# ── TC-AR-5: 재고 부족 + 재확인 거절 → REJECTED ──────────────────────────────

def test_approve_insufficient_then_reject(
    approve_reject_ctrl, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 2)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, "거절", 0)
    approve_reject_ctrl.run()
    assert order_model.get_by_id(order["id"])["status"] == "REJECTED"


# ── TC-AR-6: 처리 후 show_approve_result 호출 (order_no, status 전달) ─────────

def test_approve_result_shown_after_confirm(
    approve_reject_ctrl, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 10)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, 0)
    approve_reject_ctrl.run()
    assert view.approve_result is not None
    order_no, status = view.approve_result
    assert order_no == order["order_no"]
    assert status == "CONFIRMED"


# ── TC-AR-7: 0 입력 → 처리 없이 종료 ─────────────────────────────────────────

def test_zero_exits_without_processing(
    approve_reject_ctrl, order_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(0)
    approve_reject_ctrl.run()
    assert order_model.get_by_id(order["id"])["status"] == "RESERVED"

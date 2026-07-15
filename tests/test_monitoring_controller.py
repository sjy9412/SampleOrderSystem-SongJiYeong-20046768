from __future__ import annotations
import pytest
from unittest.mock import patch
from models.order import OrderModel
from models.inventory import InventoryModel
from models.sample import SampleModel
from controllers.monitoring_controller import MonitoringController


class StubMonitoringView:
    def __init__(self):
        self.shown_order_counts = None
        self.shown_inventory_status = None
        self.invalid_input_called = False
        self._choices: list[str] = []

    def show_menu(self) -> None:
        pass

    def get_menu_choice(self) -> str:
        return self._choices.pop(0)

    def show_order_counts(self, counts: dict) -> None:
        self.shown_order_counts = counts

    def show_inventory_status(self, items: list[dict]) -> None:
        self.shown_inventory_status = items

    def show_error(self, message: str) -> None:
        pass

    def show_invalid_input(self) -> None:
        self.invalid_input_called = True

    def show_exit(self) -> None:
        pass

    def get_title_input(self) -> str:
        return ""

    def get_id_input(self, action: str) -> str:
        return ""

    def on_model_changed(self, event) -> None:
        pass


def make_order(sample_id="s1", customer="고객", quantity=10, status="RESERVED", order_id="o1"):
    return {"id": order_id, "sample_id": sample_id, "customer_name": customer,
            "quantity": quantity, "status": status, "created_at": "2024-01-01"}


def make_stock(sample_id="s1", quantity=100, stock_id="inv1"):
    return {"id": stock_id, "sample_id": sample_id, "quantity": quantity}


def make_sample(sample_id="s1", name="시료A"):
    return {"id": sample_id, "name": name, "avg_production_time": 2.0, "yield_rate": 0.9}


# ─── 주문량 확인 ─────────────────────────────────────────────────────────────


def test_handle_order_counts_shows_counts_by_status():
    """메뉴 '1' 선택 시 상태별 주문 건수 dict가 view로 전달된다."""
    reserved = [make_order(status="RESERVED")]
    producing = [make_order(status="PRODUCING"), make_order(status="PRODUCING", order_id="o2")]
    confirmed = []
    release = [make_order(status="RELEASE", order_id="o3")]

    def fake_read_all(collection, **filters):
        if collection != "orders":
            return []
        status = filters.get("status")
        return {
            "RESERVED": reserved,
            "PRODUCING": producing,
            "CONFIRMED": confirmed,
            "RELEASE": release,
            "REJECTED": [],
        }.get(status, [])

    view = StubMonitoringView()
    view._choices = ["1", "0"]

    with patch("db.json_store.read_all", side_effect=fake_read_all):
        ctrl = MonitoringController(OrderModel(), InventoryModel(), SampleModel(), view)
        ctrl.run()

    assert view.shown_order_counts == {
        "RESERVED": 1,
        "PRODUCING": 2,
        "CONFIRMED": 0,
        "RELEASE": 1,
    }


def test_handle_order_counts_excludes_rejected():
    """REJECTED 상태는 주문량 집계에 포함되지 않는다."""
    def fake_read_all(collection, **filters):
        if collection != "orders":
            return []
        status = filters.get("status")
        if status == "REJECTED":
            return [make_order(status="REJECTED"), make_order(status="REJECTED", order_id="o2")]
        return []

    view = StubMonitoringView()
    view._choices = ["1", "0"]

    with patch("db.json_store.read_all", side_effect=fake_read_all):
        ctrl = MonitoringController(OrderModel(), InventoryModel(), SampleModel(), view)
        ctrl.run()

    assert "REJECTED" not in view.shown_order_counts


# ─── 재고량 확인 ─────────────────────────────────────────────────────────────


def test_handle_inventory_status_shows_sample_name_and_quantity():
    """메뉴 '2' 선택 시 시료명과 수량이 items에 포함된다."""
    stocks = [make_stock(sample_id="s1", quantity=50)]
    sample = make_sample(sample_id="s1", name="시료A")

    def fake_read_all(collection, **filters):
        if collection == "inventories":
            return stocks
        if collection == "orders":
            return []
        return []

    def fake_read_one(collection, record_id):
        if collection == "samples" and record_id == "s1":
            return sample
        return None

    view = StubMonitoringView()
    view._choices = ["2", "0"]

    with patch("db.json_store.read_all", side_effect=fake_read_all), \
         patch("db.json_store.read_one", side_effect=fake_read_one):
        ctrl = MonitoringController(OrderModel(), InventoryModel(), SampleModel(), view)
        ctrl.run()

    assert len(view.shown_inventory_status) == 1
    item = view.shown_inventory_status[0]
    assert item["name"] == "시료A"
    assert item["quantity"] == 50


def test_handle_inventory_status_status_is_고갈_when_zero():
    """재고 수량이 0이면 상태가 '고갈'이다."""
    stocks = [make_stock(sample_id="s1", quantity=0)]
    sample = make_sample(sample_id="s1", name="시료A")

    def fake_read_all(collection, **filters):
        if collection == "inventories":
            return stocks
        if collection == "orders":
            return []
        return []

    def fake_read_one(collection, record_id):
        if collection == "samples":
            return sample
        return None

    view = StubMonitoringView()
    view._choices = ["2", "0"]

    with patch("db.json_store.read_all", side_effect=fake_read_all), \
         patch("db.json_store.read_one", side_effect=fake_read_one):
        ctrl = MonitoringController(OrderModel(), InventoryModel(), SampleModel(), view)
        ctrl.run()

    assert view.shown_inventory_status[0]["status"] == "고갈"


def test_handle_inventory_status_status_is_부족_when_less_than_pending():
    """재고가 대기 중인 주문 수량 합계보다 적으면 상태가 '부족'이다."""
    stocks = [make_stock(sample_id="s1", quantity=5)]
    sample = make_sample(sample_id="s1", name="시료A")
    pending = [
        make_order(sample_id="s1", quantity=8, status="RESERVED"),
        make_order(sample_id="s1", quantity=4, status="PRODUCING", order_id="o2"),
    ]

    def fake_read_all(collection, **filters):
        if collection == "inventories":
            return stocks
        if collection == "orders":
            status = filters.get("status")
            if status == "RESERVED":
                return [pending[0]]
            if status == "PRODUCING":
                return [pending[1]]
            return []
        return []

    def fake_read_one(collection, record_id):
        if collection == "samples":
            return sample
        return None

    view = StubMonitoringView()
    view._choices = ["2", "0"]

    with patch("db.json_store.read_all", side_effect=fake_read_all), \
         patch("db.json_store.read_one", side_effect=fake_read_one):
        ctrl = MonitoringController(OrderModel(), InventoryModel(), SampleModel(), view)
        ctrl.run()

    assert view.shown_inventory_status[0]["status"] == "부족"


def test_handle_inventory_status_status_is_여유_when_sufficient():
    """재고가 대기 중인 주문 수량 합계 이상이면 상태가 '여유'이다."""
    stocks = [make_stock(sample_id="s1", quantity=20)]
    sample = make_sample(sample_id="s1", name="시료A")
    pending = [make_order(sample_id="s1", quantity=10, status="RESERVED")]

    def fake_read_all(collection, **filters):
        if collection == "inventories":
            return stocks
        if collection == "orders":
            status = filters.get("status")
            if status == "RESERVED":
                return pending
            return []
        return []

    def fake_read_one(collection, record_id):
        if collection == "samples":
            return sample
        return None

    view = StubMonitoringView()
    view._choices = ["2", "0"]

    with patch("db.json_store.read_all", side_effect=fake_read_all), \
         patch("db.json_store.read_one", side_effect=fake_read_one):
        ctrl = MonitoringController(OrderModel(), InventoryModel(), SampleModel(), view)
        ctrl.run()

    assert view.shown_inventory_status[0]["status"] == "여유"


# ─── 잘못된 입력 ─────────────────────────────────────────────────────────────


def test_invalid_choice_calls_show_invalid_input():
    """메뉴에 없는 선택지 입력 시 show_invalid_input()이 호출된다."""
    def fake_read_all(collection, **filters):
        return []

    view = StubMonitoringView()
    view._choices = ["9", "0"]

    with patch("db.json_store.read_all", side_effect=fake_read_all):
        ctrl = MonitoringController(OrderModel(), InventoryModel(), SampleModel(), view)
        ctrl.run()

    assert view.invalid_input_called is True

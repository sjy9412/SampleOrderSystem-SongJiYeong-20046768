import pytest
from models.order import OrderModel
from views.release_view import ReleaseView


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("orders")
    yield
    store.reset("orders")


@pytest.fixture
def order_model():
    return OrderModel()


@pytest.fixture
def view(order_model):
    return ReleaseView(order_model)


# ── TC-1: 번호·주문번호·고객·시료·수량 포함 테이블 출력 ──────────────────────────

def test_show_confirmed_orders_displays_numbered_rows(view, order_model, capsys):
    order = order_model.reserve("S-001", "홍길동", 5)
    order_model.confirm(order["id"])
    orders = order_model.get_by_status("CONFIRMED")

    view.show_confirmed_orders(orders)

    out = capsys.readouterr().out
    assert "1" in out
    assert order["order_no"] in out
    assert "홍길동" in out
    assert "S-001" in out
    assert "5" in out


# ── TC-2: CONFIRMED 없으면 안내 메시지 출력 ─────────────────────────────────────

def test_show_confirmed_orders_empty_shows_info_message(view, capsys):
    view.show_confirmed_orders([])

    out = capsys.readouterr().out
    assert "없습니다" in out


# ── TC-3: "출고처리 완료." 메시지 출력 ──────────────────────────────────────────

def test_show_release_result_displays_completion_message(view, order_model, capsys):
    order = order_model.reserve("S-001", "홍길동", 5)
    order_model.confirm(order["id"])
    released = order_model.release(order["id"])

    view.show_release_result(released)

    out = capsys.readouterr().out
    assert "출고처리 완료" in out


# ── TC-4: 주문번호·출고수량·상태 포함 출력 ──────────────────────────────────────

def test_show_release_result_displays_order_no_and_quantity(view, order_model, capsys):
    order = order_model.reserve("S-001", "홍길동", 5)
    order_model.confirm(order["id"])
    released = order_model.release(order["id"])

    view.show_release_result(released)

    out = capsys.readouterr().out
    assert released["order_no"] in out
    assert "5" in out
    assert "RELEASE" in out


# ── TC-5: 처리 일시(updated_at) 포함 출력 ───────────────────────────────────────

def test_show_release_result_displays_timestamp(view, order_model, capsys):
    order = order_model.reserve("S-001", "홍길동", 5)
    order_model.confirm(order["id"])
    released = order_model.release(order["id"])

    view.show_release_result(released)

    out = capsys.readouterr().out
    assert "처리 일시" in out

import pytest
from models.order import OrderModel
from views.order_view import OrderView


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("orders")
    yield
    store.reset("orders")


@pytest.fixture
def view():
    model = OrderModel()
    return OrderView(model)


def test_show_orders_displays_ea_unit(view, capsys):
    orders = [{"id": "O-001", "customer_name": "홍길동", "quantity": 5, "status": "RESERVED"}]
    view.show_orders(orders)
    output = capsys.readouterr().out
    assert "ea" in output


def test_get_order_input_prompt_contains_ea(view, capsys, monkeypatch):
    inputs = iter(["S-001", "홍길동", "5"])
    monkeypatch.setattr("builtins.input", lambda: next(inputs))
    view.get_order_input()
    output = capsys.readouterr().out
    assert "ea" in output


# ── 신규 뷰 메서드 테스트 ──────────────────────────────────────────────────────

def test_show_reserved_orders_numbered_includes_numbers(view, capsys):
    orders = [
        {"id": "O-1", "order_no": "ORD-20260715-0001", "customer_name": "홍길동",
         "quantity": 5, "status": "RESERVED"},
        {"id": "O-2", "order_no": "ORD-20260715-0002", "customer_name": "이순신",
         "quantity": 3, "status": "RESERVED"},
    ]
    view.show_reserved_orders_numbered(orders)
    out = capsys.readouterr().out
    assert "1" in out
    assert "2" in out
    assert "홍길동" in out


def test_show_stock_checking_shows_message(view, capsys):
    view.show_stock_checking("실리콘 웨이퍼")
    out = capsys.readouterr().out
    assert "재고 확인 중" in out
    assert "실리콘 웨이퍼" in out


def test_show_stock_detail_shows_all_fields(view, capsys):
    view.show_stock_detail("실리콘 웨이퍼", stock=3, quantity=10, shortage=7)
    out = capsys.readouterr().out
    assert "실리콘 웨이퍼" in out
    assert "3" in out
    assert "10" in out
    assert "7" in out


def test_show_approve_result_confirmed_shows_완료(view, capsys):
    view.show_approve_result("ORD-20260715-0001", "CONFIRMED")
    out = capsys.readouterr().out
    assert "승인 완료" in out
    assert "ORD-20260715-0001" in out
    assert "CONFIRMED" in out


def test_show_approve_result_rejected_shows_거절(view, capsys):
    view.show_approve_result("ORD-20260715-0001", "REJECTED")
    out = capsys.readouterr().out
    assert "승인 거절" in out
    assert "ORD-20260715-0001" in out
    assert "REJECTED" in out

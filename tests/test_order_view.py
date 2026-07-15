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

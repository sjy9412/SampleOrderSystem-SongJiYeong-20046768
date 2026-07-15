import pytest
from unittest.mock import MagicMock
from views.production_view import ProductionView


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("orders")
    store.reset("samples")
    store.reset("production_queue")
    yield
    store.reset("orders")
    store.reset("samples")
    store.reset("production_queue")


@pytest.fixture
def view():
    model = MagicMock()
    return ProductionView(model)


def test_show_current_displays_min_unit(view, capsys):
    info_data = {
        "order_id": "O-001",
        "sample_name": "TestChip",
        "quantity": 5,
        "actual_qty": 6,
        "total_time": 12.0,
    }
    view.show_current(info_data)
    output = capsys.readouterr().out
    assert "min" in output


def test_show_queue_displays_ea_unit(view, capsys):
    items = [{
        "position": 1,
        "order_id": "O-001",
        "sample_name": "TestChip",
        "customer_name": "홍길동",
        "quantity": 5,
    }]
    view.show_queue(items)
    output = capsys.readouterr().out
    assert "ea" in output

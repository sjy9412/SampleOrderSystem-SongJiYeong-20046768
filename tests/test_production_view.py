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


SAMPLE_INFO = {
    "order_id": "O-001",
    "order_no": "ORD-20260715-0001",
    "sample_name": "TestChip",
    "quantity": 100,
    "stock": 20,
    "shortage": 80,
    "yield_rate": 0.89,
    "avg_time": 1.9,
    "actual_qty": 90,
    "total_time": 171.0,
    "progress_pct": 45.0,
    "estimated_completion": "2026-07-15 14:30",
}

SAMPLE_QUEUE = [{
    "position": 1,
    "order_no": "ORD-20260715-0001",
    "sample_name": "TestChip",
    "customer_name": "홍길동",
    "quantity": 100,
    "shortage": 80,
    "actual_qty": 90,
    "estimated_completion": "2026-07-15 14:30",
}]


def test_show_current_displays_min_unit(view, capsys):
    view.show_current(SAMPLE_INFO)
    output = capsys.readouterr().out
    assert "min" in output


def test_show_current_displays_stock_and_shortage(view, capsys):
    view.show_current(SAMPLE_INFO)
    output = capsys.readouterr().out
    assert "재고" in output
    assert "부족" in output


def test_show_current_displays_yield_info(view, capsys):
    view.show_current(SAMPLE_INFO)
    output = capsys.readouterr().out
    assert "수율" in output


def test_show_current_displays_progress_pct(view, capsys):
    view.show_current(SAMPLE_INFO)
    output = capsys.readouterr().out
    assert "%" in output


def test_show_current_displays_estimated_completion(view, capsys):
    view.show_current(SAMPLE_INFO)
    output = capsys.readouterr().out
    assert "완료 예정" in output


def test_show_queue_displays_ea_unit(view, capsys):
    view.show_queue(SAMPLE_QUEUE)
    output = capsys.readouterr().out
    assert "ea" in output


def test_show_queue_displays_order_no(view, capsys):
    view.show_queue(SAMPLE_QUEUE)
    output = capsys.readouterr().out
    assert "ORD-" in output  # UUID가 아닌 주문번호 형식 확인


def test_show_queue_displays_shortage(view, capsys):
    view.show_queue(SAMPLE_QUEUE)
    output = capsys.readouterr().out
    assert "80" in output


def test_show_queue_displays_actual_qty(view, capsys):
    view.show_queue(SAMPLE_QUEUE)
    output = capsys.readouterr().out
    assert "90" in output


def test_show_queue_displays_estimated_completion(view, capsys):
    view.show_queue(SAMPLE_QUEUE)
    output = capsys.readouterr().out
    assert "완료 예정" in output or "2026-07-15" in output

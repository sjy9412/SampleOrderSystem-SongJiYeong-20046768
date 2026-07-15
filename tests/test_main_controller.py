from __future__ import annotations

import pytest
from unittest.mock import patch

from controllers.main_controller import MainController
from app import create_app


# ──────────────────────────────────────────────
# 대시보드 테스트용 Fake 모델
# ──────────────────────────────────────────────

class FakeSampleModel:
    def get_all(self): return [{"id": "S-001"}, {"id": "S-002"}]

class FakeInventoryModel:
    def get_all_stocks(self): return [{"quantity": 10}, {"quantity": 5}]

class FakeOrderModel:
    def get_all(self): return [{"id": "o1"}, {"id": "o2"}, {"id": "o3"}]

class FakeProductionLine:
    def get_queue(self): return [{"order_id": "o1"}]


def _dashboard_ctrl():
    return MainController(
        [],
        sample_model=FakeSampleModel(),
        inventory_model=FakeInventoryModel(),
        order_model=FakeOrderModel(),
        production_line=FakeProductionLine(),
    )


def test_dashboard_shows_sample_count(capsys):
    ctrl = _dashboard_ctrl()
    with patch("builtins.input", return_value="0"):
        ctrl.run()
    assert "2종" in capsys.readouterr().out


def test_dashboard_shows_total_stock(capsys):
    ctrl = _dashboard_ctrl()
    with patch("builtins.input", return_value="0"):
        ctrl.run()
    assert "15ea" in capsys.readouterr().out


def test_dashboard_shows_order_count(capsys):
    ctrl = _dashboard_ctrl()
    with patch("builtins.input", return_value="0"):
        ctrl.run()
    assert "3건" in capsys.readouterr().out


def test_dashboard_shows_production_queue_count(capsys):
    ctrl = _dashboard_ctrl()
    with patch("builtins.input", return_value="0"):
        ctrl.run()
    assert "1건 대기" in capsys.readouterr().out


# ──────────────────────────────────────────────
# 기존 테스트
# ──────────────────────────────────────────────

class StubController:
    def __init__(self):
        self.called = False

    def run(self):
        self.called = True


def test_exits_on_zero():
    ctrl = MainController([])
    with patch("builtins.input", return_value="0"):
        ctrl.run()


def test_dispatches_to_first_sub_controller():
    stub = StubController()
    ctrl = MainController([stub])
    with patch("builtins.input", side_effect=["1", "0"]):
        ctrl.run()
    assert stub.called


def test_invalid_input_shows_invalid_message(capsys):
    ctrl = MainController([])
    with patch("builtins.input", side_effect=["9", "0"]):
        ctrl.run()
    assert "잘못된" in capsys.readouterr().out


def test_create_app_returns_object_with_run():
    app = create_app()
    assert hasattr(app, "run") and callable(app.run)

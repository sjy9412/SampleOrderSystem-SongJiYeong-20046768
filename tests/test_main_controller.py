from __future__ import annotations

import pytest
from unittest.mock import patch

from controllers.main_controller import MainController
from app import create_app


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


def test_invalid_input_shows_invalid_message():
    ctrl = MainController([])
    output = []
    with patch("builtins.input", side_effect=["9", "0"]):
        with patch("builtins.print", side_effect=lambda *a, **k: output.append(" ".join(str(x) for x in a))):
            ctrl.run()
    assert any("잘못된" in line for line in output)


def test_create_app_returns_object_with_run():
    app = create_app()
    assert hasattr(app, "run") and callable(app.run)

from __future__ import annotations

import pytest
from unittest.mock import patch


def test_prompt_choice_shows_arrow_format(capsys, monkeypatch):
    monkeypatch.setattr("builtins.input", lambda: "1")
    from views.display import prompt_choice
    prompt_choice()
    out = capsys.readouterr().out
    assert "선택 >" in out

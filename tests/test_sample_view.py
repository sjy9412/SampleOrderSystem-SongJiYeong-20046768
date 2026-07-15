import pytest
from models.sample import SampleModel
from views.sample_view import SampleView


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("samples")
    yield
    store.reset("samples")


@pytest.fixture
def view():
    model = SampleModel()
    return SampleView(model)


def test_show_samples_uses_min_unit_in_column_header(view, capsys):
    samples = [{"id": "S-001", "name": "TestChip", "avg_production_time": 2.5, "yield_rate": 0.95}]
    view.show_samples(samples, {})
    output = capsys.readouterr().out
    assert "min" in output


def test_get_sample_input_prompt_contains_min(view, capsys, monkeypatch):
    inputs = iter(["TestChip", "2.5", "0.95"])
    monkeypatch.setattr("builtins.input", lambda: next(inputs))
    view.get_sample_input()
    output = capsys.readouterr().out
    assert "min" in output

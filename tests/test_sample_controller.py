import pytest
from models.sample import SampleModel
from controllers.sample_controller import SampleController


class MockSampleView:
    def __init__(self):
        self.shown_samples = None
        self._choices = iter(['0'])
        self._sample_input = None
        self._keyword = None
        self.invalid_input_shown = False

    def show_menu(self): pass
    def get_menu_choice(self): return next(self._choices)
    def get_sample_input(self): return self._sample_input
    def get_search_keyword(self): return self._keyword
    def show_samples(self, samples, stocks): self.shown_samples = samples
    def show_error(self, msg): pass
    def show_invalid_input(self): self.invalid_input_shown = True
    def show_exit(self): pass
    def on_model_changed(self, event): pass
    def get_title_input(self): return ""
    def get_id_input(self, action): return ""


@pytest.fixture(autouse=True)
def clean_db():
    from db import json_store as store
    store.reset("samples")
    yield
    store.reset("samples")


@pytest.fixture
def model():
    return SampleModel()


@pytest.fixture
def view():
    return MockSampleView()


def test_register_adds_sample_to_model(model, view):
    view._choices = iter(['1', '0'])
    view._sample_input = ("TestChip", 2.5, 0.9)
    SampleController(model, view).run()
    samples = model.get_all()
    assert len(samples) == 1
    assert samples[0]["name"] == "TestChip"
    assert samples[0]["avg_production_time"] == 2.5
    assert samples[0]["yield_rate"] == 0.9


def test_list_passes_all_samples_to_view(model, view):
    model.add("ChipA", 1.0, 0.8)
    model.add("ChipB", 2.0, 0.9)
    view._choices = iter(['2', '0'])
    SampleController(model, view).run()
    assert view.shown_samples is not None
    assert len(view.shown_samples) == 2


def test_search_passes_matching_samples_to_view(model, view):
    model.add("AlphaChip", 1.0, 0.8)
    model.add("BetaChip", 2.0, 0.9)
    view._choices = iter(['3', '0'])
    view._keyword = "Alpha"
    SampleController(model, view).run()
    assert view.shown_samples is not None
    assert len(view.shown_samples) == 1
    assert view.shown_samples[0]["name"] == "AlphaChip"


def test_invalid_choice_shows_invalid_input(model, view):
    view._choices = iter(['X', '0'])
    SampleController(model, view).run()
    assert view.invalid_input_shown is True

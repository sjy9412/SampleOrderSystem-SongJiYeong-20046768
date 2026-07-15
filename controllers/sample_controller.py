from __future__ import annotations


class SampleController:

    def __init__(self, model, inventory_model, view) -> None:
        self._model = model
        self._inventory_model = inventory_model
        self._view = view

    def run(self) -> None:
        while True:
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == '0':
                break
            elif choice == '1':
                self._handle_register()
            elif choice == '2':
                self._handle_list()
            elif choice == '3':
                self._handle_search()
            else:
                self._view.show_invalid_input()

    def _handle_register(self) -> None:
        name, avg_time, yield_rate = self._view.get_sample_input()
        try:
            self._model.add(name, avg_time, yield_rate)
        except ValueError as e:
            self._view.show_error(str(e))

    def _handle_list(self) -> None:
        samples = self._model.get_all()
        stocks = {s["sample_id"]: s["quantity"] for s in self._inventory_model.get_all_stocks()}
        self._view.show_samples(samples, stocks)

    def _handle_search(self) -> None:
        keyword = self._view.get_search_keyword()
        samples = self._model.search(keyword)
        stocks = {s["sample_id"]: s["quantity"] for s in self._inventory_model.get_all_stocks()}
        self._view.show_samples(samples, stocks)

from __future__ import annotations
from views.display import separator


class ProductionController:

    def __init__(self, production_line, view) -> None:
        self._production_line = production_line
        self._view = view

    def run(self) -> None:
        first = True
        while True:
            if not first:
                separator()
            first = False
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            if choice == "0":
                break
            elif choice == "1":
                separator()
                self._handle_current()
            elif choice == "2":
                separator()
                self._handle_queue()
            else:
                self._view.show_invalid_input()

    def _handle_current(self) -> None:
        info = self._production_line.get_current_info()
        if info is None:
            self._view.show_no_current()
        else:
            self._view.show_current(info)

    def _handle_queue(self) -> None:
        items = self._production_line.get_queue_info()
        self._view.show_queue(items)

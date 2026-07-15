from __future__ import annotations
from models.todo_model import TodoModel
from views.base import BaseView


class TodoController:
    """
    사용자 입력을 받아 Model 을 조작하는 흐름 제어 담당.
    - View 는 BaseView 인터페이스로만 참조 → 어떤 View 구현체든 주입 가능.
    - Model 변경 결과 피드백은 Observer 경로(Model→View)로 전달되므로
      Controller 는 결과를 직접 View 에 전달하지 않는다.
    """

    def __init__(self, model: TodoModel, view: BaseView) -> None:
        self._model = model
        self._view = view
        self._running = False
        self._handlers = {
            "1": self._handle_list,
            "2": self._handle_add,
            "3": self._handle_toggle,
            "4": self._handle_delete,
            "0": self._handle_exit,
        }

    # ── 메인 루프 ─────────────────────────────────────────────────────────
    def run(self) -> None:
        self._running = True
        while self._running:
            self._view.show_menu()
            choice = self._view.get_menu_choice()
            handler = self._handlers.get(choice)
            if handler:
                handler()
            else:
                self._view.show_invalid_input()

    # ── 핸들러 ────────────────────────────────────────────────────────────
    def _handle_list(self) -> None:
        todos = self._model.get_all()
        if not todos:
            self._view.show_error("항목이 없습니다.")
            return
        for t in todos:
            status = "[O]" if t.done else "[ ]"
            print(f"    {t.id:>2}  {status}  {t.title}")

    def _handle_add(self) -> None:
        title = self._view.get_title_input()
        try:
            self._model.add(title)          # 결과는 Observer 경로로 View 에 전달
        except ValueError as e:
            self._view.show_error(str(e))

    def _handle_toggle(self) -> None:
        raw = self._view.get_id_input("완료 토글")
        todo_id = self._parse_id(raw)
        if todo_id is None:
            return
        try:
            self._model.toggle_done(todo_id)
        except KeyError as e:
            self._view.show_error(str(e))

    def _handle_delete(self) -> None:
        raw = self._view.get_id_input("삭제")
        todo_id = self._parse_id(raw)
        if todo_id is None:
            return
        try:
            self._model.delete(todo_id)
        except KeyError as e:
            self._view.show_error(str(e))

    def _handle_exit(self) -> None:
        self._view.show_exit()
        self._running = False

    # ── 유틸 ──────────────────────────────────────────────────────────────
    def _parse_id(self, raw: str) -> int | None:
        try:
            return int(raw)
        except ValueError:
            self._view.show_invalid_input()
            return None

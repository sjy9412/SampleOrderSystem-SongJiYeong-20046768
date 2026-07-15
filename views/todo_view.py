from models.base import ModelEvent, EventType
from models.todo_model import TodoModel


class TodoView:
    """
    기본 View — todo_table_view 의 단순화 버전.
    하위 호환을 위해 유지한다.
    """

    def __init__(self, model: TodoModel) -> None:
        self._model = model
        model.subscribe(self)

    def on_model_changed(self, event: ModelEvent) -> None:
        todo = event.payload
        label = {EventType.ADDED: "추가", EventType.TOGGLED: "변경", EventType.DELETED: "삭제"}[event.type]
        print(f"  [{label}] {todo.title}")

    def show_menu(self) -> None:
        print("\n========== Todo 목록 관리 ==========")
        print("  1. 목록 보기  2. 항목 추가")
        print("  3. 완료 토글  4. 항목 삭제  0. 종료")
        print("====================================")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def get_title_input(self) -> str:
        return input("제목 입력 > ").strip()

    def get_id_input(self, action: str) -> str:
        return input(f"{action}할 ID 입력 > ").strip()

    def show_error(self, message: str) -> None:
        print(f"\n[오류] {message}")

    def show_invalid_input(self) -> None:
        print("\n[잘못된 입력입니다]")

    def show_exit(self) -> None:
        print("\n종료합니다.")

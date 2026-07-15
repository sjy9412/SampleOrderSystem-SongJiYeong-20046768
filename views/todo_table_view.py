from models.base import ModelEvent, EventType
from models.todo_model import Todo, TodoModel


class TodoTableView:
    """
    [View A] 상세 테이블 형식으로 전체 목록을 출력.
    Model 이벤트를 수신해 변경 직후 자동으로 전체 목록을 갱신한다.
    """

    def __init__(self, model: TodoModel) -> None:
        self._model = model
        model.subscribe(self)           # Observer 등록

    # ── ModelObserver 구현 ────────────────────────────────────────────────
    def on_model_changed(self, event: ModelEvent) -> None:
        label = {
            EventType.ADDED:   "추가됨",
            EventType.TOGGLED: "변경됨",
            EventType.DELETED: "삭제됨",
        }[event.type]
        todo: Todo = event.payload
        state = ""
        if event.type == EventType.TOGGLED:
            state = " -> " + ("완료" if todo.done else "미완료")
        print(f"  [이벤트] {label}: [{todo.id}] {todo.title}{state}")
        self._render_table()

    # ── Controller 호출 계약 ──────────────────────────────────────────────
    def show_menu(self) -> None:
        print("\n┌─────────────────────────────────────┐")
        print("│       Todo 관리  (Table View)        │")
        print("├─────────────────────────────────────┤")
        print("│  1. 목록 보기   2. 항목 추가         │")
        print("│  3. 완료 토글   4. 항목 삭제         │")
        print("│  0. 종료                             │")
        print("└─────────────────────────────────────┘")

    def get_menu_choice(self) -> str:
        return input("선택 > ").strip()

    def get_title_input(self) -> str:
        return input("제목 입력 > ").strip()

    def get_id_input(self, action: str) -> str:
        return input(f"{action}할 ID > ").strip()

    def show_error(self, message: str) -> None:
        print(f"  [오류] {message}")

    def show_invalid_input(self) -> None:
        print("  [잘못된 입력]")

    def show_exit(self) -> None:
        print("  종료합니다.")

    # ── 내부 렌더링 ───────────────────────────────────────────────────────
    def _render_table(self) -> None:
        todos = self._model.get_all()
        if not todos:
            print("  (항목 없음)")
            return
        print(f"\n  {'ID':>3}  {'상태':^4}  제목")
        print("  " + "-" * 30)
        for t in todos:
            status = "[O]" if t.done else "[ ]"
            print(f"  {t.id:>3}  {status}  {t.title}")

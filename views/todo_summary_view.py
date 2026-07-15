from models.base import ModelEvent, EventType
from models.todo_model import TodoModel


class TodoSummaryView:
    """
    [View B] 숫자 요약만 보여주는 최소 뷰.
    TableView 와 완전히 동일한 인터페이스를 구현하므로
    Controller 코드를 한 줄도 바꾸지 않고 교체할 수 있다.
    """

    def __init__(self, model: TodoModel) -> None:
        self._model = model
        model.subscribe(self)

    # ── ModelObserver 구현 ────────────────────────────────────────────────
    def on_model_changed(self, event: ModelEvent) -> None:
        action = {
            EventType.ADDED:   "항목 추가",
            EventType.TOGGLED: "상태 변경",
            EventType.DELETED: "항목 삭제",
        }[event.type]
        total = self._model.count
        done  = self._model.done_count
        pct   = int(done / total * 100) if total else 0
        bar   = "#" * (pct // 10) + "." * (10 - pct // 10)
        print(f"  [요약] {action} | 전체 {total}개 | 완료 {done}개 | [{bar}] {pct}%")

    # ── Controller 호출 계약 ──────────────────────────────────────────────
    def show_menu(self) -> None:
        total = self._model.count
        done  = self._model.done_count
        print(f"\n=== Todo (Summary View) | 전체:{total} 완료:{done} 미완료:{total-done} ===")
        print("  1.목록  2.추가  3.토글  4.삭제  0.종료")

    def get_menu_choice(self) -> str:
        return input("> ").strip()

    def get_title_input(self) -> str:
        return input("제목: ").strip()

    def get_id_input(self, action: str) -> str:
        return input(f"{action} ID: ").strip()

    def show_error(self, message: str) -> None:
        print(f"  ERR: {message}")

    def show_invalid_input(self) -> None:
        print("  ERR: 잘못된 입력")

    def show_exit(self) -> None:
        print("  bye.")

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from models.base import ObservableModel, ModelEvent, EventType


@dataclass
class Todo:
    id: int
    title: str
    done: bool = False


class TodoModel(ObservableModel):
    """
    데이터 저장소 및 비즈니스 로직 담당.
    View / Controller 를 전혀 import 하지 않는다.
    상태가 바뀔 때마다 ModelEvent 를 발행해 구독자에게 알린다.
    """

    def __init__(self) -> None:
        super().__init__()
        self._todos: list[Todo] = []
        self._next_id: int = 1

    # ── 조회 (읽기 전용 — 이벤트 없음) ──────────────────────────────────
    def get_all(self) -> list[Todo]:
        return list(self._todos)

    def get_by_id(self, todo_id: int) -> Optional[Todo]:
        return next((t for t in self._todos if t.id == todo_id), None)

    @property
    def count(self) -> int:
        return len(self._todos)

    @property
    def done_count(self) -> int:
        return sum(1 for t in self._todos if t.done)

    # ── 변경 (이벤트 발행) ────────────────────────────────────────────────
    def add(self, title: str) -> Todo:
        if not title.strip():
            raise ValueError("제목은 비워둘 수 없습니다.")
        todo = Todo(id=self._next_id, title=title.strip())
        self._todos.append(todo)
        self._next_id += 1
        self._notify(ModelEvent(EventType.ADDED, todo))
        return todo

    def toggle_done(self, todo_id: int) -> Todo:
        todo = self._get_or_raise(todo_id)
        todo.done = not todo.done
        self._notify(ModelEvent(EventType.TOGGLED, todo))
        return todo

    def delete(self, todo_id: int) -> Todo:
        todo = self._get_or_raise(todo_id)
        self._todos.remove(todo)
        self._notify(ModelEvent(EventType.DELETED, todo))
        return todo

    # ── 내부 헬퍼 ─────────────────────────────────────────────────────────
    def _get_or_raise(self, todo_id: int) -> Todo:
        todo = self.get_by_id(todo_id)
        if todo is None:
            raise KeyError(f"ID {todo_id}에 해당하는 항목이 없습니다.")
        return todo

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol


class EventType(Enum):
    ADDED   = auto()
    TOGGLED = auto()
    DELETED = auto()


@dataclass(frozen=True)
class ModelEvent:
    type: EventType
    payload: Any  # 변경된 도메인 객체


class ModelObserver(Protocol):
    """Model 변경 알림을 받을 객체가 구현해야 하는 인터페이스."""
    def on_model_changed(self, event: ModelEvent) -> None: ...


class ObservableModel:
    """Observer 등록/해제 및 알림 발송 기능을 제공하는 베이스 클래스."""

    def __init__(self) -> None:
        self._observers: list[ModelObserver] = []

    def subscribe(self, observer: ModelObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: ModelObserver) -> None:
        self._observers.remove(observer)

    def _notify(self, event: ModelEvent) -> None:
        for obs in self._observers:
            obs.on_model_changed(event)

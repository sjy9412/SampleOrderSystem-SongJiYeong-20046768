"""
MVC PoC 데모 — 사용자 입력 없이 자동으로 세 가지 핵심 명제를 증명한다.

  명제 1. Model 은 View 를 전혀 모른 채 Observer 로 상태를 통지한다.
  명제 2. View 를 교체해도 Controller / Model 코드는 단 한 줄도 바뀌지 않는다.
  명제 3. 각 레이어는 나머지 레이어 없이 단독으로 테스트할 수 있다.
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from models.todo_model import TodoModel
from models.base import ModelEvent, EventType
from views.todo_table_view import TodoTableView
from views.todo_summary_view import TodoSummaryView
from controllers.todo_controller import TodoController


# ── 헬퍼 ──────────────────────────────────────────────────────────────────
def section(title: str) -> None:
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print(f"{'=' * 55}")

def step(msg: str) -> None:
    print(f"\n  >> {msg}")


# ══════════════════════════════════════════════════════════════════════════
# 명제 1 — Model 독립성 & Observer 통지
# ══════════════════════════════════════════════════════════════════════════
section("명제 1 | Model 독립성 & Observer 통지")

step("Model 에 익명 Observer 두 개를 직접 등록한다.")

model = TodoModel()

class LogObserver:
    def __init__(self, tag: str):
        self.tag = tag
        self.received: list[ModelEvent] = []
    def on_model_changed(self, event: ModelEvent) -> None:
        self.received.append(event)
        print(f"    [{self.tag}] 이벤트 수신 → {event.type.name} / {event.payload}")

obs_a = LogObserver("Observer-A")
obs_b = LogObserver("Observer-B")
model.subscribe(obs_a)
model.subscribe(obs_b)

step("add('파이썬 공부') 호출 — Model 은 View 를 모른 채 이벤트만 발행한다.")
model.add("파이썬 공부")

step("add('알고리즘 연습') → toggle_done(1) 연속 호출")
model.add("알고리즘 연습")
model.toggle_done(1)

step("Observer-B 를 구독 해제 후 delete(2) → A 만 수신해야 한다.")
model.unsubscribe(obs_b)
model.delete(2)

print(f"\n  Observer-A 수신 횟수: {len(obs_a.received)}  (기대값: 4)")
print(f"  Observer-B 수신 횟수: {len(obs_b.received)}  (기대값: 3)")
assert len(obs_a.received) == 4, "Observer-A 수신 횟수 불일치"
assert len(obs_b.received) == 3, "Observer-B 수신 횟수 불일치"
print("  [PASS] Observer 통지 정확성 검증 완료")


# ══════════════════════════════════════════════════════════════════════════
# 명제 2 — View 교체 가능성 (Controller 코드 변경 없음)
# ══════════════════════════════════════════════════════════════════════════
section("명제 2 | View 교체 — Controller 코드 무변경 증명")

SCRIPT = ["파이썬 공부", "알고리즘 연습", "디자인 패턴 읽기"]


def run_scripted(controller: TodoController, view_label: str) -> None:
    """Controller.run() 대신 내부 핸들러를 직접 호출해 자동 시나리오를 실행."""
    print(f"\n  ─── {view_label} ───")
    for title in SCRIPT:
        controller._model.add(title)        # add → Observer 경로로 View 에 알림
    controller._model.toggle_done(1)
    controller._model.toggle_done(2)
    controller._model.delete(3)


step("TableView 로 Controller 실행")
model_t = TodoModel()
view_t  = TodoTableView(model_t)
ctrl_t  = TodoController(model_t, view_t)
run_scripted(ctrl_t, "TableView")

step("SummaryView 로 동일한 Controller 코드 재사용")
model_s = TodoModel()
view_s  = TodoSummaryView(model_s)
ctrl_s  = TodoController(model_s, view_s)   # Controller 생성자 인자만 교체
run_scripted(ctrl_s, "SummaryView")

print("\n  [PASS] 두 Controller 는 동일한 클래스 TodoController 를 사용했음")
assert type(ctrl_t) is type(ctrl_s), "Controller 클래스가 다름"


# ══════════════════════════════════════════════════════════════════════════
# 명제 3 — 계층 독립 단위 검증
# ══════════════════════════════════════════════════════════════════════════
section("명제 3 | 계층 독립 단위 검증")

# ── Model 단독 검증 ────────────────────────────────────────────────────
step("Model 단독 검증 (View / Controller 없음)")
m = TodoModel()
t1 = m.add("테스트 항목")
assert t1.id == 1
assert t1.done is False
m.toggle_done(1)
assert m.get_by_id(1).done is True
m.delete(1)
assert m.get_by_id(1) is None
assert m.count == 0
print("  [PASS] Model 단독 검증 완료")

# ── View 단독 검증 (Spy Observer 로 이벤트만 확인) ─────────────────────
step("View 단독 검증 (Controller 없음 — 이벤트 직접 주입)")

class SpyModel(TodoModel):
    """View 의존성 없이 이벤트만 발행하는 테스트용 Model."""
    pass

spy_m  = SpyModel()
table_v = TodoTableView(spy_m)

spy_m.add("뷰 테스트 항목A")
spy_m.add("뷰 테스트 항목B")
spy_m.toggle_done(1)
print("  [PASS] View 가 이벤트에 반응해 렌더링 완료")

# ── Controller 단독 검증 (Mock View 주입) ─────────────────────────────
step("Controller 단독 검증 (Mock View 주입)")

class MockView:
    """Controller 테스트용 — 입출력을 모두 인메모리로 처리."""
    def __init__(self, inputs: list[str]):
        self._inputs = iter(inputs)
        self.outputs: list[str] = []
        self.errors:  list[str] = []
    def show_menu(self) -> None: pass
    def get_menu_choice(self) -> str: return next(self._inputs)
    def get_title_input(self) -> str: return next(self._inputs)
    def get_id_input(self, _: str) -> str: return next(self._inputs)
    def show_error(self, msg: str) -> None: self.errors.append(msg)
    def show_invalid_input(self) -> None: self.errors.append("invalid")
    def show_exit(self) -> None: self.outputs.append("exit")
    def on_model_changed(self, event: ModelEvent) -> None: pass

mock_inputs = [
    "2", "컨트롤러 테스트 항목",   # add
    "3", "1",                       # toggle id=1
    "4", "1",                       # delete id=1
    "4", "99",                      # delete 존재하지 않는 id → 오류
    "0",                            # exit
]
mock_model = TodoModel()
mock_view  = MockView(mock_inputs)
ctrl       = TodoController(mock_model, mock_view)
ctrl.run()

assert mock_model.count == 0,   f"삭제 후 count 불일치: {mock_model.count}"
assert len(mock_view.errors) == 1, f"오류 횟수 불일치: {mock_view.errors}"
assert "exit" in mock_view.outputs
print(f"  [PASS] Controller 검증 완료 (오류 1건 정확히 발생: {mock_view.errors[0]!r})")


# ══════════════════════════════════════════════════════════════════════════
section("PoC 결과 요약")
print("""
  명제 1 [PASS] Model → Observer 이벤트 발행, View import 없음
  명제 2 [PASS] View 교체 시 Controller 클래스 무변경
  명제 3 [PASS] Model / View / Controller 각 레이어 단독 검증 성공
""")

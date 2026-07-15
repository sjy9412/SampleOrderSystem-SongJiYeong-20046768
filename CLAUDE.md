# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**반도체 시료 생산주문 관리 시스템** — 콘솔 기반의 시료 주문·생산 관리 시스템.  
MVC 구조를 활용해 시스템을 개발한다.

### 업무 흐름

```
고객 (이메일 요청) → 주문 담당자 (주문서 작성) → 생산 담당자 (승인/거절)
```

주문 상태: `RESERVED → PRODUCING → CONFIRMED → RELEASE` (거절 시 `REJECTED`)

생산 라인 특성: 라인 하나당 시료 하나씩 순차 생산, 주문된 시료만 생산.

### 메인 메뉴 항목

시료관리 / 시료 주문 / 주문 승인·거절 / 모니터링 / 생산라인 조회 / 출고 처리

---

## 실행 명령

```bash
# 애플리케이션 실행
python main.py           # 기본 테이블 뷰
python main.py summary   # 요약 뷰

# JSON DB 모니터 REPL (Rich 기반 읽기 전용 뷰어)
python db/main.py              # db/db.json 연결
python db/main.py path/to.json  # 파일 지정

# 테스트
pytest                          # 전체
pytest path/to/test_file.py     # 파일 단위
pytest path/to/test_file.py::test_name  # 단일 케이스
pytest -x                       # 첫 실패에서 중단
pytest -v                       # 상세 출력
```

Windows 환경에서 한글 출력이 깨질 경우 `main.py`처럼 `sys.stdout`을 UTF-8로 래핑한다.

---

## 아키텍처

### 레이어 구조

```
controllers/   ← 사용자 입력 수신 → Model 조작
models/        ← 도메인 로직 + Observer 이벤트 발행 (View 미참조)
views/         ← Model 이벤트 수신 → 화면 렌더링 + 사용자 입력 수집
db/            ← JSON 파일 영속성 레이어
```

### 핵심 패턴: MVC + Observer

**Model → View 통지 경로**

- `models/base.py`: `ObservableModel`(subscribe/unsubscribe/\_notify), `ModelEvent`(frozen dataclass), `ModelObserver`(Protocol)
- Model은 상태 변경 시 `_notify(ModelEvent)`를 호출하고, 구독한 View가 `on_model_changed(event)`로 수신한다.
- Controller는 Model 변경 결과를 View에 직접 전달하지 않는다. Observer 경로로만 흐른다.

**View 인터페이스**

- `views/base.py`: `BaseView` — `ModelObserver` + Controller가 호출하는 UI 계약 (`show_menu`, `get_menu_choice`, `show_error` 등)
- View는 생성자에서 `model.subscribe(self)`로 자기 자신을 등록한다.
- View 구현체를 교체해도 Controller·Model 코드는 한 줄도 바뀌지 않는다.

**Rich 콘솔 유틸리티 (`views/display.py`)**

모든 View가 공유하는 Rich 기반 렌더링 모듈. `db/monitor/display.py`와 동일한 패턴.

```python
from views.display import (
    console,          # Rich Console 인스턴스 (공유)
    print_table,      # Rich ROUNDED 테이블 출력 (status 컬럼 자동 색상)
    show_menu_panel,  # Panel 형태의 번호 메뉴
    prompt_choice,    # 선택 프롬프트 → str 반환
    prompt_input,     # 레이블 프롬프트 → str 반환
    section,          # 구분선 (console.rule)
    success, error, info, warn,  # 아이콘 포함 상태 메시지
)
```

- `print_table`에 `col_labels` 딕셔너리를 넘기면 컬럼 헤더를 한국어로 바꿀 수 있다.
- `status` 키를 가진 컬럼은 주문 상태에 따라 자동 색상 적용 (`_STATUS_STYLES`).
- View에서 `print()` / `input()`을 직접 사용하지 않는다. 반드시 이 모듈의 함수를 사용한다.

**Controller**

- `app.py`의 `create_app()`이 Model·View·Controller를 조립해 반환한다.
- Controller는 `BaseView` 인터페이스만 알며, 구현체에 의존하지 않는다.

### 영속성 레이어 (`db/json_store.py`)

컬렉션 기반 JSON CRUD. 레코드마다 UUID `id`, `created_at`, `updated_at` 자동 부여.

```python
from db import json_store as store
store.create("orders", {"sample_id": "...", "status": "RESERVED"})
store.read_all("orders", status="RESERVED")
store.read_one("orders", record_id)
store.update("orders", record_id, {"status": "PRODUCING"})
store.delete("orders", record_id)
store.reset("orders")   # 컬렉션 전체 삭제
```

`db/dummy_generator.py`에서 Faker 기반 더미 데이터를 일괄 생성할 수 있다(`bulk_insert`). 개발·테스트 초기에 샘플 데이터를 채울 때 사용한다.

---

## TDD 워크플로우

이 저장소는 `/test-driven-development` 스킬을 사용한다. 모든 기능 구현 전에 반드시 실패하는 테스트를 먼저 작성한다.

```
RED (실패 테스트 작성 + tmp/Plan.md) → 사용자 검토·승인 → GREEN (최소 구현) → REVIEW → 커밋
```

- 테스트가 먼저 실패하는 것을 직접 확인하지 않으면 GREEN으로 진행하지 않는다.
- mock은 외부 경계(파일 I/O, 시간 등)에서만 사용한다. 내부 레이어 간 호출은 실제 객체를 사용한다.
- View 출력 검증 시 `builtins.print`를 mock하지 않는다. Rich는 `console.print()`로 stdout에 직접 쓰므로 `capsys` fixture로 캡처한다.

```python
def test_shows_error(capsys):
    ...
    assert "잘못된" in capsys.readouterr().out
```

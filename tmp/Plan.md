# TDD Plan — 출고 처리 UX 개선

## 목표 (Goal)

출고 처리 메뉴 진입 시 서브 메뉴 없이 바로 CONFIRMED 주문 목록(번호·주문번호·고객·시료·수량)을 표시하고,  
번호 선택으로 출고를 실행하면 "출고처리 완료." 메시지와 함께 주문번호·출고수량·처리일시·상태를 보여준다.

---

## 변경 범위

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `docs/PRD.md` | 문서 | 출고 처리 섹션 상세화 (완료) |
| `controllers/release_controller.py` | 교체 | 서브 메뉴 제거 → 자동 목록 + 번호 선택 플로우 |
| `views/release_view.py` | 교체 | `show_menu`/`get_menu_choice` 제거 → `show_confirmed_orders` / `get_release_number` / `show_release_result` |
| `tests/test_release_controller.py` | 교체 | 새 플로우에 맞는 테스트로 전면 교체 |

---

## 신규 인터페이스 설계

### Controller (`ReleaseController.run`)

```python
def run(self) -> None:
    orders = self._order.get_by_status("CONFIRMED")
    self._view.show_confirmed_orders(orders)
    if not orders:
        return
    choice = self._view.get_release_number(len(orders))
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(orders):
            self._view.show_error("유효하지 않은 번호입니다.")
            return
        released = self._order.release(orders[idx]["id"])
        self._view.show_release_result(released)
    except (ValueError, KeyError) as e:
        self._view.show_error(str(e))
```

### View 신규 메서드

| 메서드 | 역할 |
|--------|------|
| `show_confirmed_orders(orders)` | 번호·주문번호·고객·시료·수량 테이블 출력 |
| `get_release_number(count)` | "출고할 번호를 입력하세요:" 프롬프트 → str |
| `show_release_result(order)` | "출고처리 완료." + 주문번호·출고수량·처리일시·상태 |

제거 메서드: `show_menu`, `get_menu_choice`, `get_order_id`, `get_title_input`, `get_id_input`

---

## TDD 사이클 계획

---

### 사이클 1: 컨트롤러 새 플로우

**테스트 파일:** `tests/test_release_controller.py`

| 테스트 | 검증 내용 |
|--------|-----------|
| `test_shows_confirmed_orders_immediately_on_entry` | run() 호출 시 view.shown_orders에 CONFIRMED 주문이 담김 |
| `test_no_confirmed_orders_returns_immediately` | CONFIRMED 없으면 view.release_result가 None |
| `test_release_by_number_transitions_to_release` | 번호 "1" 입력 → order status == "RELEASE" |
| `test_shows_release_result_after_processing` | 완료 후 view.release_result["status"] == "RELEASE" |
| `test_invalid_number_shows_error` | 범위 밖 번호 입력 → view.errors에 오류 메시지 |

**Stub 변경:**
```python
class ReleaseViewStub:
    def show_confirmed_orders(self, orders): self.shown_orders = list(orders)
    def get_release_number(self, count): return self._next()
    def show_release_result(self, order): self.release_result = order
    def show_error(self, message): self.errors.append(message)
    def on_model_changed(self, event): pass
```

**예상 실패 이유:** `ReleaseController`에 `show_confirmed_orders`, `get_release_number`, `show_release_result` 미존재

**구현 방향:** `run()` 메서드를 새 플로우로 교체, `_handle_list_confirmed` / `_handle_release` 제거

---

### 사이클 2: 뷰 — 번호 포함 CONFIRMED 목록 표시

**테스트 파일:** `tests/test_release_view.py` (신규)

| 테스트 | 검증 내용 |
|--------|-----------|
| `test_show_confirmed_orders_displays_header_and_rows` | "번호" / order_no / customer_name / sample_id / quantity 모두 출력에 포함 |
| `test_show_confirmed_orders_empty_shows_info_message` | 빈 목록이면 "출고 가능한 주문이 없습니다." 출력 |

**예상 실패 이유:** `ReleaseView.show_confirmed_orders` 미존재

**구현 방향:**
```python
def show_confirmed_orders(self, orders):
    section("출고 가능 주문 목록")
    if not orders:
        info("출고 가능한 주문이 없습니다.")
        return
    rows = [
        {"번호": str(i+1), "주문번호": o["order_no"],
         "고객": o["customer_name"], "시료": o["sample_id"],
         "수량": f"{o['quantity']} ea"}
        for i, o in enumerate(orders)
    ]
    print_table(rows)
```

---

### 사이클 3: 뷰 — 출고 결과 표시

**테스트 파일:** `tests/test_release_view.py`

| 테스트 | 검증 내용 |
|--------|-----------|
| `test_show_release_result_displays_completion_message` | "출고처리 완료" in output |
| `test_show_release_result_displays_order_no_and_quantity` | order_no / quantity / "RELEASE" in output |
| `test_show_release_result_displays_timestamp` | updated_at 기반 처리일시 in output |

**예상 실패 이유:** `ReleaseView.show_release_result` 미존재

**구현 방향:**
```python
def show_release_result(self, order):
    success("출고처리 완료.")
    # 주문번호, 출고수량, 처리일시, 상태 테이블 출력
```

---

## 커밋 계획

1. `plan: 출고 처리 UX 개선 TDD 계획 + PRD 업데이트`
2. `feat: 출고 처리 컨트롤러 새 플로우 (자동 목록 + 번호 선택)`
3. `feat: 출고 처리 뷰 — 번호 포함 목록 / 결과 표시`

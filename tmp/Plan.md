# STEP 8 — 모니터링 View / Controller TDD Plan

## 목표 (Goal)

주문량(상태별)과 재고 현황(시료별)을 조회하는 모니터링 화면을 TDD로 구현한다.

---

## 구현 파일

| 파일 | 역할 |
|------|------|
| `views/monitoring_view.py` | 모니터링 화면 출력 + 입력 수집 |
| `controllers/monitoring_controller.py` | 메뉴 라우팅 + 데이터 집계 |
| `tests/test_monitoring_controller.py` | 컨트롤러 동작 테스트 |

---

## 설계 요약

### MonitoringView

MonitoringController 생성자: (order_model, inventory_model, sample_model, view)
MonitoringView 생성자: () - 모델 구독 불필요, 온디맨드 조회

show_order_counts(counts): counts = {'RESERVED': 3, 'PRODUCING': 1, 'CONFIRMED': 5, 'RELEASE': 2}
show_inventory_status(items): items = [{'name': 'AAA', 'quantity': 100, 'status': '여유'}, ...]

---

## 재고 상태 계산 로직

pending_qty = sum(quantity for orders where sample_id==X and status in [RESERVED, PRODUCING])
status = inventory_model.get_status(sample_id, pending_qty)

get_status 내부:
  quantity == 0            -> "고갈"
  quantity <  pending_qty  -> "부족"
  quantity >= pending_qty  -> "여유"

---

## 테스트 케이스 목록

1. test_handle_order_counts_shows_counts_by_status
   - 메뉴 '1' -> 각 상태별 주문 건수가 counts dict로 전달됨

2. test_handle_order_counts_excludes_rejected
   - REJECTED 주문은 counts에 포함되지 않음

3. test_handle_inventory_status_shows_sample_name_and_quantity
   - 메뉴 '2' -> 시료명 수량이 items에 포함됨

4. test_handle_inventory_status_status_is_고갈_when_zero
   - 재고 0 -> 상태 "고갈"

5. test_handle_inventory_status_status_is_부족_when_less_than_pending
   - 재고 < 대기주문 합계 -> "부족"

6. test_handle_inventory_status_status_is_여유_when_sufficient
   - 재고 >= 대기주문 합계 -> "여유"

7. test_invalid_choice_calls_show_invalid_input
   - 잘못된 선택 -> show_invalid_input() 호출

---

## 모킹 전략

- db.json_store 함수를 unittest.mock.patch로 패치 -> 파일 I/O 없음
- 내부 레이어(Model 객체)는 실제 객체 사용
- 뷰는 StubMonitoringView 스텁 사용 (화면 I/O 제거)

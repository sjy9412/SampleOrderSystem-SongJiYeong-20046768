# TDD Plan — 생산현황 · 대기 주문 목록 표시 정보 확장

## 목표 (Goal)

생산라인 조회 화면의 두 기능을 확장한다.

### 생산 현황 (show_current)
현재 표시 항목: 주문 ID · 시료명 · 주문 수량 · 실 생산량 · 총 생산시간  
**추가 표시 항목:** 재고 · 부족분 · 수율/min · 진행율(%) · 완료 예정 시간

표시 형식 예시:
```
주문번호    ORD-20260715-0001
시료명      게르마늄 웨이퍼-6인치
주문량      100 ea
재고        20 ea
부족분      80 ea
실 생산량   90 ea  (수율 89% / 1.9 min)
진행율      45.0%
완료 예정   2026-07-15 14:30
```

### 대기 주문 목록 (show_queue)
현재 컬럼: 순번 · 주문 ID(UUID) · 시료명 · 고객명 · 수량  
**변경 컬럼:** 순번 · 주문번호(order_no) · 시료명 · 주문량 · 부족분 · 실생산량 · 예상 완료 시간

---

## 변경 범위

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `models/production_line.py` | 확장 | `get_current_info(now=)`, `get_queue_info(now=)` |
| `views/production_view.py` | 확장 | `show_current()`, `show_queue()` |
| `docs/PRD.md` | 문서 | 생산 현황 · 대기 주문 확인 섹션 |
| `tests/test_production_line.py` | 새 테스트 추가 | |
| `tests/test_production_view.py` | 새 테스트 추가 + 기존 테스트 픽스처 보완 | |
| `tests/test_production_controller.py` | 기존 테스트 수정 | order_id → order_no |

---

## 설계 결정

### 시간 주입 (`now` 파라미터)
`get_current_info(now=None)`과 `get_queue_info(now=None)`은 테스트 시 `now`를 주입받는다.  
`None`이면 `datetime.now(timezone.utc)`를 사용한다.

### 진행율(progress_pct) 계산
```
elapsed_min  = (now - queue_item.created_at).total_seconds() / 60
progress_pct = min(100.0, elapsed_min / total_time * 100)
```
- `created_at` = 생산 큐에 enqueue된 시각 (생산 시작 기준)
- `total_time` = 0 이면 progress_pct = 100.0

### 완료 예정 시간(estimated_completion) 계산
```
# 현재 생산 중 (position=1)
completion = queue_item.created_at + timedelta(minutes=total_time)

# 대기 항목 (position >= 2): 앞 항목 완료 시각 + 자신의 total_time
completion_n = completion_{n-1} + timedelta(minutes=total_time_n)
```
- 반환 형식: `"YYYY-MM-DD HH:MM"` (로컬 시각, `astimezone()` 사용)

### `get_queue_info()` dict 변경
| 기존 키 | 신규 키 | 비고 |
|---------|---------|------|
| `order_id` | `order_no` | UUID → 주문번호 문자열 |
| (없음) | `shortage` | 부족분 |
| (없음) | `actual_qty` | 실생산량 |
| (없음) | `estimated_completion` | 예상 완료 시간 문자열 |

기존 테스트 `test_queue_shows_waiting_orders_in_order`의  
`view.shown_queue[0]["order_id"]` 검증을 `["order_no"]`로 변경한다.

---

## TDD 사이클 계획

### 사이클 1: `get_current_info()` 확장 (모델)

**테스트 파일:** `tests/test_production_line.py`

| 테스트 | 검증 내용 |
|--------|-----------|
| `test_get_current_info_includes_stock_and_shortage` | `info["stock"]`, `info["shortage"]` |
| `test_get_current_info_includes_yield_rate_and_avg_time` | `info["yield_rate"]`, `info["avg_time"]` |
| `test_get_current_info_includes_order_no` | `info["order_no"].startswith("ORD-")` |
| `test_get_current_info_calculates_progress_pct` | `now` 주입 → `info["progress_pct"] ≈ 50.0` |
| `test_get_current_info_includes_estimated_completion` | `"estimated_completion"` in info (문자열 확인) |

**구현:** `get_current_info(self, now=None)` 반환 dict 확장

---

### 사이클 2: `get_queue_info()` 확장 (모델)

**테스트 파일:** `tests/test_production_line.py`

| 테스트 | 검증 내용 |
|--------|-----------|
| `test_get_queue_info_includes_order_no` | `queue[0]["order_no"]` == order["order_no"] |
| `test_get_queue_info_includes_shortage_and_actual_qty` | `queue[0]["shortage"]`, `queue[0]["actual_qty"]` |
| `test_get_queue_info_cumulative_estimated_completion` | position-2 아이템의 예상 완료 시각이 position-1보다 늦음 |

**구현:** `get_queue_info(self, now=None)` 반환 dict 확장  
**기존 테스트 수정:** `test_production_controller.py` — `order_id` → `order_no`

---

### 사이클 3: `show_current()` 뷰 업데이트

**테스트 파일:** `tests/test_production_view.py`

| 테스트 | 검증 내용 |
|--------|-----------|
| `test_show_current_displays_stock_and_shortage` | "재고", "부족" in output |
| `test_show_current_displays_yield_info` | "수율" in output |
| `test_show_current_displays_progress_pct` | "%" in output |
| `test_show_current_displays_estimated_completion` | "완료 예정" in output |

기존 `test_show_current_displays_min_unit` — info_data에 신규 필드 추가

---

### 사이클 4: `show_queue()` 뷰 업데이트

**테스트 파일:** `tests/test_production_view.py`

| 테스트 | 검증 내용 |
|--------|-----------|
| `test_show_queue_displays_order_no` | ORD- 형식 문자열 in output |
| `test_show_queue_displays_shortage` | shortage 숫자 in output |
| `test_show_queue_displays_actual_qty` | actual_qty 숫자 in output |
| `test_show_queue_displays_estimated_completion` | "완료 예정" in output |

기존 `test_show_queue_displays_ea_unit` — item dict에 신규 필드 추가

---

### 사이클 5: PRD.md 업데이트

생산 현황 · 대기 주문 확인 섹션을 새 명세로 교체한다.

---

## 예상 실패 이유

- 사이클 1: `info.get("stock")` → `None` (키 없음)
- 사이클 2: `queue[0].get("order_no")` → `None` (키 없음)
- 사이클 3: output에 "재고", "수율" 등 문자열 없음
- 사이클 4: output에 ORD- 형식, 부족분 숫자 없음

# 구현 계획 — 반도체 시료 생산주문 관리 시스템

> PRD 기반 순차 구현 계획. 각 단계는 이전 단계가 완료된 후 진행한다.  
> 모든 구현은 **TDD 워크플로우** (RED → GREEN → REVIEW → COMMIT) 를 따른다.

---

## 현재 상태

| 항목 | 상태 |
|------|------|
| MVC 기반 구조 (ObservableModel, BaseView, Controller 루프) | ✅ 완료 |
| DB 영속성 계층 (`db/json_store.py`) | ✅ 완료 |
| 더미 데이터 생성기 (`db/dummy_generator.py`) | ✅ 완료 |
| DataMonitor REPL (`db/monitor/`) | ✅ 완료 |
| Sample / Order / 생산 라인 / 재고 / 메인 메뉴 | ❌ 미구현 |

---

## 구현 단계

### STEP 1 — 시료(Sample) 모델

**목표**: 시스템의 가장 기본 단위인 시료 도메인을 구현한다.

**구현 파일**
- `models/sample.py`

**데이터 구조**

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | str (UUID) | 시료 고유 식별자 |
| `name` | str | 시료 이름 |
| `avg_production_time` | float | 평균 생산시간 (시간 단위) |
| `yield_rate` | float | 수율 (0.0 ~ 1.0) |

**구현 기능**

| 메서드 | 설명 |
|--------|------|
| `add(name, avg_production_time, yield_rate)` | 시료 등록, ADDED 이벤트 발행 |
| `get_all()` | 전체 시료 목록 반환 |
| `get_by_id(sample_id)` | ID로 시료 단건 조회 |
| `search(keyword)` | 이름 기준 검색 |

**이벤트 타입 추가**: `ADDED`, `LISTED`, `SEARCHED`

---

### STEP 2 — 시료 관리 View / Controller

**목표**: 시료 등록, 조회, 검색 기능을 사용자에게 노출한다.

**구현 파일**
- `views/sample_view.py`
- `controllers/sample_controller.py`

**메뉴 구성**

```
[시료 관리]
1. 시료 등록
2. 시료 목록 조회
3. 시료 검색
0. 뒤로
```

**View 계약 (`views/base.py` 확장 또는 별도 프로토콜)**

| 메서드 | 설명 |
|--------|------|
| `get_sample_input()` | 이름, 평균 생산시간, 수율 입력 수신 |
| `get_search_keyword()` | 검색어 입력 수신 |
| `show_samples(samples, stocks)` | 시료 목록 + 재고 수량 출력 |

**Controller 핸들러**

| 선택 | 핸들러 | 동작 |
|------|--------|------|
| `1` | `_handle_register` | `SampleModel.add()` 호출 |
| `2` | `_handle_list` | `SampleModel.get_all()` 호출 |
| `3` | `_handle_search` | `SampleModel.search()` 호출 |

> ⚠️ **미완성**: `_handle_list` / `_handle_search` 에서 `show_samples(samples, stocks)` 의 `stocks` 인자를 빈 dict `{}`로 고정 전달 중.  
> `SampleController` 에 `InventoryModel` 을 주입해 실제 재고 수량을 함께 표시해야 한다.

---

### STEP 3 — 주문(Order) 모델

**목표**: 주문 도메인과 상태 전이 로직을 구현한다.

**구현 파일**
- `models/order.py`

**데이터 구조**

| 필드 | 타입 | 설명 |
|------|------|------|
| `id` | str (UUID) | 주문 고유 식별자 |
| `sample_id` | str | 주문한 시료 ID |
| `customer_name` | str | 고객명 |
| `quantity` | int | 주문 수량 |
| `status` | str | `RESERVED` \| `PRODUCING` \| `CONFIRMED` \| `RELEASE` \| `REJECTED` |

**주문 상태 전이**

```
RESERVED ──승인(재고 충분)──→ CONFIRMED ──출고──→ RELEASE
         ──승인(재고 부족)──→ PRODUCING ──생산완료──→ CONFIRMED
         ──거절──────────→ REJECTED
```

**구현 기능**

| 메서드 | 설명 |
|--------|------|
| `reserve(sample_id, customer_name, quantity)` | 주문 생성 (RESERVED), ADDED 이벤트 |
| `get_reserved()` | RESERVED 상태 주문 목록 |
| `get_by_status(status)` | 상태별 주문 목록 |
| `confirm(order_id)` | CONFIRMED 전환 |
| `reject(order_id)` | REJECTED 전환 |
| `set_producing(order_id)` | PRODUCING 전환 |
| `release(order_id)` | RELEASE 전환 |

---

### STEP 4 — 재고(Inventory) 모델

**목표**: 시료별 재고 수량을 관리하고 주문 대비 상태를 판단한다.

**구현 파일**
- `models/inventory.py`

**데이터 구조**

| 필드 | 타입 | 설명 |
|------|------|------|
| `sample_id` | str | 시료 ID |
| `quantity` | int | 현재 재고 수량 |

**재고 상태 판단 로직**

| 상태 | 조건 |
|------|------|
| 고갈 | `quantity == 0` |
| 부족 | `quantity < 주문 수량` |
| 여유 | `quantity >= 주문 수량` |

**구현 기능**

| 메서드 | 설명 |
|--------|------|
| `get_stock(sample_id)` | 특정 시료의 현재 재고 반환 |
| `get_all_stocks()` | 전체 시료 재고 목록 반환 |
| `is_sufficient(sample_id, quantity)` | 재고 충분 여부 판단 |
| `decrease(sample_id, quantity)` | 재고 차감 |
| `increase(sample_id, quantity)` | 재고 증가 (생산 완료 시) |
| `get_status(sample_id, ordered_quantity)` | 여유/부족/고갈 상태 반환 |

---

### STEP 5 — 주문 승인/거절 View / Controller

**목표**: RESERVED 주문 목록을 확인하고, 승인·거절을 처리한다.  
승인 시 재고 상황에 따라 자동으로 CONFIRMED 또는 PRODUCING으로 분기한다.

**구현 파일**
- `views/order_view.py`
- `controllers/order_controller.py`

**메뉴 구성**

```
[주문 관리]
1. 주문 접수 (예약)
2. 주문 승인/거절
0. 뒤로
```

**승인/거절 흐름 (Controller 내부)**

```
_handle_approve_reject():
  1. get_reserved() → show_orders()
  2. get_order_id() → 주문 선택
  3. get_approve_or_reject() → "승인" or "거절"
     - "거절" → reject()  # REJECTED
     - "승인" + 재고 충분 → decrease() + confirm()  # CONFIRMED
     - "승인" + 재고 부족 → show_stock_insufficient()
                           → get_approve_or_reject() 재확인
                             - "승인" → set_producing() + enqueue()  # PRODUCING
                             - "거절" → reject()  # REJECTED
```

---

### STEP 6 — 생산 라인(ProductionLine) 모델

**목표**: FIFO 생산 큐를 관리하고, 생산량 산정 및 완료 처리를 구현한다.

**구현 파일**
- `models/production_line.py`

**생산량 산정 공식**

```
부족분      = 주문 수량 - 현재 재고
실 생산량   = ceil(부족분 / 수율)
총 생산시간 = 평균 생산시간 × 실 생산량
```

**구현 기능**

| 메서드 | 설명 |
|--------|------|
| `enqueue(order_id)` | 생산 대기열에 주문 추가 (FIFO) |
| `get_queue()` | 현재 대기 주문 목록 반환 |
| `get_current()` | 현재 생산 중인 주문 정보 반환 |
| `complete(order_id)` | 생산 완료 처리 → 재고 증가, 주문 CONFIRMED 전환 |
| `calculate_production(shortage, yield_rate, avg_time)` | 실 생산량·총 생산시간 계산 |

---

### STEP 7 — 생산 라인 View / Controller

**목표**: 생산 현황과 대기 큐를 화면에 표시한다.

**구현 파일**
- `views/production_view.py`
- `controllers/production_controller.py`

**메뉴 구성**

```
[생산 라인]
1. 생산 현황 조회
2. 대기 주문 목록
0. 뒤로
```

**표시 정보**

| 항목 | 내용 |
|------|------|
| 생산 현황 | 주문 ID, 시료명, 주문 수량, 실 생산량, 총 생산시간 |
| 대기 큐 | 순번, 주문 ID, 시료명, 고객명, 주문 수량 |

---

### STEP 8 — 모니터링 View / Controller

**목표**: 주문량 및 재고 현황을 한눈에 파악할 수 있는 대시보드를 제공한다.

**구현 파일**
- `views/monitoring_view.py`
- `controllers/monitoring_controller.py`

**메뉴 구성**

```
[모니터링]
1. 주문량 확인 (상태별)
2. 재고량 확인 (시료별)
0. 뒤로
```

**주문량 표시**

| 상태 | 건수 |
|------|------|
| RESERVED | N건 |
| PRODUCING | N건 |
| CONFIRMED | N건 |
| RELEASE | N건 |

> REJECTED는 표시하지 않는다.

**재고량 표시**

| 시료명 | 재고 수량 | 상태 |
|--------|-----------|------|
| AAA | 100 | 여유 |
| BBB | 3 | 부족 |
| CCC | 0 | 고갈 |

---

### STEP 9 — 출고 처리 View / Controller

**목표**: CONFIRMED 상태의 주문을 선택해 출고(RELEASE)로 전환한다.

**구현 파일**
- `views/release_view.py`
- `controllers/release_controller.py`

**메뉴 구성**

```
[출고 처리]
1. 출고 가능 주문 목록 (CONFIRMED)
2. 출고 처리
0. 뒤로
```

**출고 처리 로직**

```python
def _handle_release(order_id):
    order_model.release(order_id)    # CONFIRMED → RELEASE
```

---

### STEP 10 — 메인 메뉴 통합

**목표**: 모든 컨트롤러를 하나의 메인 루프로 통합한다.

**수정 파일**
- `app.py` — 전체 Model / View / Controller 조립
- `main.py` — 진입점 (기존 UTF-8 설정 유지)

**메인 메뉴 구성**

```
[메인 메뉴]
1. 시료 관리
2. 주문 (접수 / 승인 / 거절)
3. 모니터링
4. 출고 처리
5. 생산 라인
0. 종료
```

**app.py 조립 구조**

```python
def create_app():
    # Models
    sample_model    = SampleModel()
    order_model     = OrderModel()
    inventory_model = InventoryModel()
    production_line = ProductionLine(order_model, inventory_model, sample_model)

    # Controllers (각 하위 메뉴)
    sample_ctrl     = SampleController(sample_model, SampleView(sample_model))
    order_ctrl      = OrderController(order_model, inventory_model, production_line, OrderView(order_model))
    monitoring_ctrl = MonitoringController(order_model, inventory_model, MonitoringView(...))
    release_ctrl    = ReleaseController(order_model, ReleaseView(order_model))
    production_ctrl = ProductionController(production_line, ProductionView(production_line))

    return MainController([sample_ctrl, order_ctrl, monitoring_ctrl, release_ctrl, production_ctrl])
```

---

## 단계별 체크리스트

| 단계 | 내용 | 상태 |
|------|------|------|
| STEP 1 | Sample 모델 | ⬜ |
| STEP 2 | 시료 관리 View / Controller | ⬜ |
| STEP 3 | Order 모델 | ⬜ |
| STEP 4 | Inventory 모델 | ✅ |
| STEP 5 | 주문 승인/거절 View / Controller | ⬜ |
| STEP 6 | ProductionLine 모델 | ⬜ |
| STEP 7 | 생산 라인 View / Controller | ⬜ |
| STEP 8 | 모니터링 View / Controller | ⬜ |
| STEP 9 | 출고 처리 View / Controller | ⬜ |
| STEP 10 | 메인 메뉴 통합 | ⬜ |

---

## 파일 구조 (완성 기준)

```
SampleOrderSystem/
├── app.py                          # 전체 조립
├── main.py                         # 진입점
├── models/
│   ├── base.py                     # ObservableModel (기존)
│   ├── sample.py                   # STEP 1
│   ├── order.py                    # STEP 3
│   ├── inventory.py                # STEP 4
│   └── production_line.py          # STEP 6
├── views/
│   ├── base.py                     # BaseView (기존)
│   ├── sample_view.py              # STEP 2
│   ├── order_view.py               # STEP 5
│   ├── monitoring_view.py          # STEP 8
│   ├── release_view.py             # STEP 9
│   └── production_view.py          # STEP 7
├── controllers/
│   ├── sample_controller.py        # STEP 2
│   ├── order_controller.py         # STEP 5
│   ├── monitoring_controller.py    # STEP 8
│   ├── release_controller.py       # STEP 9
│   ├── production_controller.py    # STEP 7
│   └── main_controller.py          # STEP 10
├── db/
│   └── (기존 유지)
└── tests/
    ├── test_sample_model.py        # STEP 1
    ├── test_order_model.py         # STEP 3
    ├── test_inventory_model.py     # STEP 4
    └── test_production_line.py     # STEP 6
```

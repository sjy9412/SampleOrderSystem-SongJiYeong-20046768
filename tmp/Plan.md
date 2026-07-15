# TDD Plan — 주문 승인/거절 UI 흐름 개선

## 목표

`ApproveRejectController.run()` 진입 시 서브메뉴 없이 RESERVED 주문 목록을
번호와 함께 즉시 표시하고, 번호 선택 → 재고 확인 → 결과 표시까지
새 UX 흐름으로 전환한다.

---

## 현재 문제

| 항목 | 현재 | 목표 |
|------|------|------|
| 진입 화면 | 서브메뉴 (1.주문처리 / 0.뒤로) | RESERVED 목록 즉시 표시 |
| 주문 선택 | 주문 ID 텍스트 입력 | 목록 번호 입력 |
| 재고 확인 시점 | 승인 선택 후 | 번호 선택 직후 |
| 재고 정보 표시 | 재고 수량, 주문 수량만 | 재고 확인 중..., 시료명, 재고, 주문수량, 부족수량 |
| 처리 결과 | 별도 표시 없음 | 승인완료/거절, 주문번호, 상태 표시 |
| 재고 충분 시 | 승인 버튼 클릭 필요 | 즉시 자동 CONFIRMED |

---

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `controllers/approve_reject_controller.py` | 서브메뉴 제거, 번호 선택, sample_model 주입 |
| `views/order_view.py` | 신규 메서드 4개 추가, 기존 불필요 메서드 제거 |
| `app.py` | ApproveRejectController에 sample_model 전달 |
| `tests/test_order_controller.py` | Stub 업데이트, 기존 TC-2~6 재작성, TC-AR-* 추가 |
| `tests/test_order_view.py` | 뷰 신규 메서드 테스트 추가 |

---

## Cycle 1 — View 신규 메서드

### 작성할 테스트 (`tests/test_order_view.py` 추가)

```python
def test_show_reserved_orders_numbered_includes_numbers(view, capsys):
    orders = [
        {"id": "O-1", "order_no": "ORD-20260715-0001", "customer_name": "홍길동",
         "quantity": 5, "status": "RESERVED"},
        {"id": "O-2", "order_no": "ORD-20260715-0002", "customer_name": "이순신",
         "quantity": 3, "status": "RESERVED"},
    ]
    view.show_reserved_orders_numbered(orders)
    out = capsys.readouterr().out
    assert "1" in out
    assert "2" in out
    assert "홍길동" in out


def test_show_stock_checking_shows_message(view, capsys):
    view.show_stock_checking("실리콘 웨이퍼")
    out = capsys.readouterr().out
    assert "재고 확인 중" in out
    assert "실리콘 웨이퍼" in out


def test_show_stock_detail_shows_all_fields(view, capsys):
    view.show_stock_detail("실리콘 웨이퍼", stock=3, quantity=10, shortage=7)
    out = capsys.readouterr().out
    assert "실리콘 웨이퍼" in out
    assert "3" in out   # 현재 재고
    assert "10" in out  # 주문 수량
    assert "7" in out   # 부족 수량


def test_show_approve_result_confirmed_shows_완료(view, capsys):
    view.show_approve_result("ORD-20260715-0001", "CONFIRMED")
    out = capsys.readouterr().out
    assert "승인 완료" in out
    assert "ORD-20260715-0001" in out
    assert "CONFIRMED" in out


def test_show_approve_result_rejected_shows_거절(view, capsys):
    view.show_approve_result("ORD-20260715-0001", "REJECTED")
    out = capsys.readouterr().out
    assert "승인 거절" in out
    assert "ORD-20260715-0001" in out
    assert "REJECTED" in out
```

### 예상 실패 이유

`OrderView`에 `show_reserved_orders_numbered`, `show_stock_checking`,
`show_stock_detail`, `show_approve_result` 메서드가 없어 `AttributeError`.

### 구현 방향 (`views/order_view.py`)

```python
def show_reserved_orders_numbered(self, orders: list[dict]) -> None:
    section("승인 대기 주문 목록")
    if not orders:
        info("대기 중인 주문이 없습니다.")
        return
    rows = [
        {
            "번호": str(i),
            "주문번호": o["order_no"],
            "고객명": o["customer_name"],
            "수량": f"{o['quantity']} ea",
            "status": o["status"],
        }
        for i, o in enumerate(orders, 1)
    ]
    print_table(rows, col_labels={"status": "상태"})

def show_stock_checking(self, sample_name: str) -> None:
    info(f"재고 확인 중... [bold]{sample_name}[/bold]")

def show_stock_detail(
    self, sample_name: str, stock: int, quantity: int, shortage: int
) -> None:
    from rich.table import Table
    from rich import box as rbox
    t = Table(box=rbox.ROUNDED, border_style="bright_black", show_header=True)
    t.add_column("항목"); t.add_column("수량")
    t.add_row("시료 이름", sample_name)
    t.add_row("현재 재고", f"{stock} ea")
    t.add_row("주문 수량", f"{quantity} ea")
    t.add_row("부족 수량", f"[bold red]{shortage} ea[/bold red]" if shortage else "0 ea")
    console.print(t)

def show_approve_result(self, order_no: str, status: str) -> None:
    from views.display import _STATUS_STYLES
    if status == "REJECTED":
        error(f"승인 거절  주문번호: [bold cyan]{order_no}[/bold cyan]")
    else:
        success(f"승인 완료  주문번호: [bold cyan]{order_no}[/bold cyan]")
    style = _STATUS_STYLES.get(status, "")
    console.print(f"  상태: [{style}]{status}[/{style}]")
```

---

## Cycle 2 — Controller 신규 흐름

### 작성할 테스트 (`tests/test_order_controller.py` 수정)

#### Stub 변경사항

```python
class OrderViewStub:
    def __init__(self, model):
        # 기존 유지 + 추가
        self.shown_reserved_numbered = []
        self.stock_checking_name = None
        self.stock_detail_params = None
        self.approve_result = None

    # 추가
    def show_reserved_orders_numbered(self, orders):
        self.shown_reserved_numbered = list(orders)

    def get_order_number_choice(self, count):
        return self._next()   # int 반환

    def show_stock_checking(self, sample_name):
        self.stock_checking_name = sample_name

    def show_stock_detail(self, sample_name, stock, quantity, shortage):
        self.stock_detail_params = dict(
            sample_name=sample_name, stock=stock,
            quantity=quantity, shortage=shortage
        )

    def show_approve_result(self, order_no, status):
        self.approve_result = (order_no, status)

    # 삭제 (더 이상 불필요)
    # show_approve_reject_menu → 유지(하위 호환, pass)
    # get_order_id → 유지(하위 호환, pass)
```

#### 테스트 케이스 재작성

```python
# TC-AR-1: 진입 시 RESERVED 목록 즉시 표시 (서브메뉴 없음)
def test_run_immediately_shows_reserved_orders(approve_reject_ctrl, order_model, sample_model, view):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(0)   # 바로 0 → 나가기
    approve_reject_ctrl.run()
    assert len(view.shown_reserved_numbered) == 1


# TC-AR-2: 재고 충분 → 즉시 CONFIRMED + 재고 차감
def test_approve_confirms_when_stock_sufficient(
    approve_reject_ctrl, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 10)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, 0)   # 첫번째 주문 선택, 이후 0 → 나가기
    approve_reject_ctrl.run()
    assert order_model.get_by_id(order["id"])["status"] == "CONFIRMED"
    assert inventory_model.get_stock(sample["id"]) == 5


# TC-AR-3: 재고 충분 → show_stock_checking, show_stock_detail 호출됨
def test_approve_sufficient_shows_stock_info(
    approve_reject_ctrl, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 10)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, 0)
    approve_reject_ctrl.run()
    assert view.stock_checking_name == "실리콘 웨이퍼"
    assert view.stock_detail_params["shortage"] == 0


# TC-AR-4: 재고 부족 + 재확인 승인 → PRODUCING + enqueue
def test_approve_sets_producing_when_stock_insufficient_and_reconfirmed(
    approve_reject_ctrl, order_model, inventory_model, production_line, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 2)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, "승인", 0)
    approve_reject_ctrl.run()
    assert order_model.get_by_id(order["id"])["status"] == "PRODUCING"
    assert order["id"] in production_line.enqueued


# TC-AR-5: 재고 부족 + 재확인 거절 → REJECTED
def test_approve_insufficient_then_reject(
    approve_reject_ctrl, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 2)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, "거절", 0)
    approve_reject_ctrl.run()
    assert order_model.get_by_id(order["id"])["status"] == "REJECTED"


# TC-AR-6: 처리 후 show_approve_result 호출 (order_no, status 전달)
def test_approve_result_shown_after_confirm(
    approve_reject_ctrl, order_model, inventory_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    inventory_model.increase(sample["id"], 10)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(1, 0)
    approve_reject_ctrl.run()
    assert view.approve_result is not None
    order_no, status = view.approve_result
    assert order_no == order["order_no"]
    assert status == "CONFIRMED"


# TC-AR-7: 0 입력 → 처리 없이 종료
def test_zero_exits_without_processing(
    approve_reject_ctrl, order_model, sample_model, view
):
    sample = sample_model.add("실리콘 웨이퍼", 5.0, 0.95)
    order = order_model.reserve(sample["id"], "홍길동", 5)
    view.set_inputs(0)
    approve_reject_ctrl.run()
    assert order_model.get_by_id(order["id"])["status"] == "RESERVED"
```

### 예상 실패 이유

- `ApproveRejectController.__init__`이 `sample_model` 인수를 받지 않음 → `TypeError`
- Stub에 `show_reserved_orders_numbered` 등 없음 → `AttributeError`
- 컨트롤러가 서브메뉴 방식이므로 `shown_reserved_numbered`가 채워지지 않음

### 구현 방향 (`controllers/approve_reject_controller.py`)

```python
class ApproveRejectController:

    def __init__(self, order_model, sample_model, inventory_model, production_line, view) -> None:
        self._order = order_model
        self._sample = sample_model
        self._inventory = inventory_model
        self._production_line = production_line
        self._view = view

    def run(self) -> None:
        while True:
            reserved = self._order.get_reserved()
            self._view.show_reserved_orders_numbered(reserved)
            if not reserved:
                break
            choice = self._view.get_order_number_choice(len(reserved))
            if choice == 0:
                break
            order = reserved[choice - 1]
            self._process_order(order)
            separator()

    def _process_order(self, order: dict) -> None:
        order_id = order["id"]
        sample_id = order["sample_id"]
        quantity = order["quantity"]

        sample = self._sample.get_by_id(sample_id)
        sample_name = sample["name"] if sample else sample_id
        stock = self._inventory.get_stock(sample_id)
        shortage = max(0, quantity - stock)

        self._view.show_stock_checking(sample_name)
        self._view.show_stock_detail(sample_name, stock, quantity, shortage)

        if shortage == 0:
            self._inventory.decrease(sample_id, quantity)
            updated = self._order.confirm(order_id)
            self._view.show_approve_result(updated["order_no"], updated["status"])
        else:
            if self._view.get_approve_or_reject() == "승인":
                self._order.set_producing(order_id)
                self._production_line.enqueue(order_id)
                updated = self._order.get_by_id(order_id)
                self._view.show_approve_result(updated["order_no"], updated["status"])
            else:
                updated = self._order.reject(order_id)
                self._view.show_approve_result(updated["order_no"], updated["status"])
```

**`app.py`:**
```python
approve_reject_ctrl = ApproveRejectController(
    order_model, sample_model, inventory_model, production_line, order_view
)
```

---

## 기존 테스트 TC-2~6 처리

기존 TC-2~6은 서브메뉴 방식(`"1"` 선택)으로 작성되어 있어 새 흐름과 맞지 않는다.
새 TC-AR-1~7로 대체하고 삭제한다.

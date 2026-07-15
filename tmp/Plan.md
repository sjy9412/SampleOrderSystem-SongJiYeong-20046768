# TDD Plan — FIFO 완료 후 다음 항목 승격 테스트

## Goal

`complete()` 호출 후 큐에서 두 번째였던 주문이 **자동으로 `get_current()`의 반환값이 되는지** 검증한다.

## 작성할 테스트

```python
def test_complete_advances_to_next_order_in_queue(
    production_line, order_model, inventory_model, sample_model
):
    sample = sample_model.add("시료M", avg_production_time=1.0, yield_rate=1.0)
    inventory_model.increase(sample["id"], 0)

    order1 = order_model.reserve(sample["id"], "첫번째", 5)
    order2 = order_model.reserve(sample["id"], "두번째", 3)
    order_model.set_producing(order1["id"])
    order_model.set_producing(order2["id"])

    production_line.enqueue(order1["id"])
    production_line.enqueue(order2["id"])

    production_line.complete(order1["id"])

    current = production_line.get_current()
    assert current is not None
    assert current["order_id"] == order2["id"]
```

## 예상 실패 이유

이 시나리오를 검증하는 테스트가 **현재 없기** 때문에 새로 추가한다.
기존 `test_complete_removes_order_from_queue`는 단일 항목만 테스트하므로 다음 항목 승격은 미검증 상태다.

> 만약 즉시 통과한다면: 구현이 이미 올바르다는 의미이고 테스트 추가 자체가 목적이므로 그대로 커밋.

## 구현 방향

- **추가 구현 코드 없음** — `complete()`가 해당 항목을 삭제하면 `get_current()`가 자연스럽게 다음 항목을 반환하는 구조가 이미 맞는지 확인하는 테스트.
- 수정 파일: `tests/test_production_line.py`의 `# ── complete ──` 섹션 끝에 추가.

## 파일

- **수정**: `tests/test_production_line.py`
- **수정 없음**: `models/production_line.py`

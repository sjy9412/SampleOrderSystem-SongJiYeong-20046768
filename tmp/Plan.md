# Plan: 시료 고유값 기준 변경 — 이름 단독

## Goal

시료 중복 판단 기준을 **이름 + 평균 생산시간 + 수율 → 이름만**으로 좁힌다.

## 변경 대상

| 파일 | 변경 내용 |
|------|-----------|
| `tests/test_sample_model.py` | 중복 관련 테스트 재편 (RED) |
| `models/sample.py` | `add()` 중복 체크 로직 단순화 (GREEN) |
| `docs/PRD.md` | "시료 중복 방지" 섹션 내용 수정 |

## 작성할 테스트 (RED)

### 추가 — `test_add_raises_when_same_name_different_attributes`

```python
def test_add_raises_when_same_name_different_attributes(model):
    model.add("ChipX", 2.5, 0.95)
    with pytest.raises(ValueError, match="이미 등록된 시료입니다."):
        model.add("ChipX", 3.0, 0.80)   # 이름 같음, 나머지 속성 다름
```

이 테스트는 현재 **실패**한다.
현재 코드는 세 속성이 모두 동일해야 중복으로 처리하므로, 생산시간·수율이 다른 경우는 등록을 허용한다.

### 수정 — `test_add_raises_when_duplicate_attributes` → `test_add_raises_when_name_is_duplicate`

테스트 이름을 의도에 맞게 변경.
내용은 동일: 이름이 같은 시료를 두 번 등록하면 ValueError 발생.

### 삭제 — `test_add_succeeds_when_only_name_differs`

새 규칙(이름 단독 고유값)과 이 테스트는 상충하지 않지만, 테스트 이름이 "이름이 달라야 별개"라는 뉘앙스를 잘못 전달한다.
이름이 다른 시료가 성공하는 케이스는 `test_get_all_returns_all_added_samples` 등 다른 테스트가 이미 커버한다.

## 예상 실패 이유

`test_add_raises_when_same_name_different_attributes`:
```
FAILED: DID NOT RAISE <class 'ValueError'>
```
현재 중복 체크가 세 속성 모두를 AND로 검사하기 때문.

## 구현 방향 (GREEN)

```python
# models/sample.py  add() 안에서
for s in existing:
    if s["name"] == name:          # 이름만 비교
        raise ValueError("이미 등록된 시료입니다.")
```

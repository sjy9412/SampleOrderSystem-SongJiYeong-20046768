# TDD Plan — 명령 전환 구분선(separator)

## 목표

메뉴 루프의 **두 번째 반복부터** `console.rule()` 구분선을 출력한다.
첫 번째 표시 전에는 구분선 없음 (배너/메뉴가 첫 진입임을 나타냄).

적용 위치:
- `MainController.run()` — 서브 컨트롤러 복귀 후 대시보드 재표시 전
- 각 서브 컨트롤러 `run()` (6개) — 다음 서브 메뉴 표시 전

## 구현 방향

`views/display.py`에 `separator()` 함수 추가:
```python
def separator() -> None:
    console.rule(style="bright_black")
```

각 컨트롤러 루프에 `first` 플래그 추가:
```python
first = True
while True:
    if not first:
        separator()
    first = False
    show_menu / _show_dashboard ...
```

## 테스트

`tests/test_main_controller.py` — 구분선 출력 확인:
```python
def test_shows_separator_between_iterations(capsys):
    stub = StubController()
    ctrl = MainController([stub])
    with patch("builtins.input", side_effect=["1", "0"]):
        ctrl.run()
    assert "─" in capsys.readouterr().out
```

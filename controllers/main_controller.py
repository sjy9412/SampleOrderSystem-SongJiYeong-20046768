from __future__ import annotations


class MainController:

    MENU = (
        "\n[메인 메뉴]\n"
        "1. 시료 관리\n"
        "2. 주문 (접수 / 승인 / 거절)\n"
        "3. 모니터링\n"
        "4. 출고 처리\n"
        "5. 생산 라인\n"
        "0. 종료\n"
    )

    def __init__(self, sub_controllers: list) -> None:
        self._controllers = sub_controllers

    def run(self) -> None:
        while True:
            print(self.MENU)
            choice = input("선택: ").strip()
            if choice == "0":
                print("시스템을 종료합니다.")
                break
            if choice.isdigit() and 1 <= int(choice) <= len(self._controllers):
                self._controllers[int(choice) - 1].run()
            else:
                print("잘못된 입력입니다.")

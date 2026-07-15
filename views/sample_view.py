from __future__ import annotations
from models.base import ModelEvent


class SampleView:

    MENU = (
        "\n[시료 관리]\n"
        "1. 시료 등록\n"
        "2. 시료 목록 조회\n"
        "3. 시료 검색\n"
        "0. 뒤로\n"
    )

    def __init__(self, model) -> None:
        model.subscribe(self)

    # ── Controller 계약 ────────────────────────────────────────────────────────

    def show_menu(self) -> None:
        print(self.MENU)

    def get_menu_choice(self) -> str:
        return input("선택: ").strip()

    def get_sample_input(self) -> tuple[str, float, float]:
        name = input("시료 이름: ").strip()
        avg_time = float(input("평균 생산시간(시간): ").strip())
        yield_rate = float(input("수율(0.0~1.0): ").strip())
        return name, avg_time, yield_rate

    def get_search_keyword(self) -> str:
        return input("검색어: ").strip()

    def show_samples(self, samples: list[dict], stocks: dict) -> None:
        if not samples:
            print("시료가 없습니다.")
            return
        header = f"{'이름':<20} {'평균 생산시간':>12} {'수율':>8} {'재고':>6}"
        print(header)
        print("-" * len(header))
        for s in samples:
            stock = stocks.get(s["id"], "-")
            print(
                f"{s['name']:<20} "
                f"{s['avg_production_time']:>12.1f} "
                f"{s['yield_rate']:>8.2f} "
                f"{stock!s:>6}"
            )

    def show_error(self, message: str) -> None:
        print(f"[오류] {message}")

    def show_invalid_input(self) -> None:
        print("잘못된 입력입니다.")

    def show_exit(self) -> None:
        print("뒤로 갑니다.")

    def get_title_input(self) -> str:
        return input("제목: ").strip()

    def get_id_input(self, action: str) -> str:
        return input(f"{action} ID: ").strip()

    # ── Observer 계약 ──────────────────────────────────────────────────────────

    def on_model_changed(self, event: ModelEvent) -> None:
        pass

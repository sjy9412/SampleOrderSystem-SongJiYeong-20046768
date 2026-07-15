from __future__ import annotations
from models.base import ModelEvent
from views.display import (
    console, print_table, show_menu_panel,
    prompt_choice, prompt_input, section,
    success, error, info, warn,
)


class SampleView:

    def __init__(self, model) -> None:
        model.subscribe(self)

    # ── Controller 계약 ────────────────────────────────────────────────────────

    def show_menu(self) -> None:
        console.print()
        show_menu_panel("시료 관리", [
            ("1", "시료 등록"),
            ("2", "시료 목록 조회"),
            ("3", "시료 검색"),
            ("0", "뒤로"),
        ])

    def get_menu_choice(self) -> str:
        return prompt_choice()

    def get_sample_input(self) -> tuple[str, float, float]:
        section("시료 등록")
        name = prompt_input("시료 이름:")
        avg_time = float(prompt_input("평균 생산시간(min/ea):"))
        yield_rate = float(prompt_input("수율(0.0~1.0):"))
        return name, avg_time, yield_rate

    def get_search_keyword(self) -> str:
        return prompt_input("검색어:")

    def show_samples(self, samples: list[dict], stocks: dict) -> None:
        section("시료 목록")
        if not samples:
            info("등록된 시료가 없습니다.")
            return
        rows = [
            {
                "이름": s["name"],
                "평균 생산시간(min/ea)": f"{s['avg_production_time']:.1f}",
                "수율": f"{s['yield_rate']:.2f}",
                "재고": str(stocks.get(s["id"], "-")),
            }
            for s in samples
        ]
        print_table(rows)

    def show_error(self, message: str) -> None:
        error(message)

    def show_invalid_input(self) -> None:
        warn("잘못된 입력입니다.")

    def show_exit(self) -> None:
        info("뒤로 갑니다.")

    def get_title_input(self) -> str:
        return prompt_input("제목:")

    def get_id_input(self, action: str) -> str:
        return prompt_input(f"{action} ID:")

    # ── Observer 계약 ──────────────────────────────────────────────────────────

    def on_model_changed(self, event: ModelEvent) -> None:
        pass

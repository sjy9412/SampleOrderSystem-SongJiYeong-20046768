# 반도체 시료 생산주문 관리 시스템

콘솔 기반의 반도체 시료 주문·생산 관리 시스템입니다.  
MVC + Observer 패턴으로 설계되었으며, JSON 파일을 영속성 레이어로 사용합니다.

---

## 업무 흐름

```
고객 (이메일 요청)
  └─▶ 주문 담당자 (주문서 작성)
        └─▶ 생산 담당자 (승인 / 거절)
```

**주문 상태 전이**

```
RESERVED → PRODUCING → CONFIRMED → RELEASE
                  └─▶ REJECTED
```

---

## 요구사항

- Python 3.10 이상
- 의존 패키지 설치

```bash
pip install -r requirements.txt
```

---

## 애플리케이션 실행

```bash
# 기본 테이블 뷰
python main.py

# 요약 뷰
python main.py summary
```

### 메인 메뉴

| 번호 | 기능 |
|------|------|
| 1 | 시료 관리 — 시료 등록·수정·삭제 |
| 2 | 시료 주문 — 신규 주문 접수 |
| 3 | 주문 승인·거절 — 대기 주문 처리 |
| 4 | 모니터링 — 주문·재고 현황 조회 |
| 5 | 생산라인 조회 — 현재 생산 중인 주문 확인 |
| 6 | 출고 처리 — 완료된 주문 출고 |

---

## 더미 데이터 생성

개발·테스트용 샘플 데이터를 빠르게 채울 때 사용합니다.  
실행 전 기존 도메인 데이터(samples / orders / inventories / production_queue)를 **전부 초기화**합니다.

```bash
# db/ 디렉토리로 이동 후 실행
cd db

# 기본값으로 생성 (시료 5개 / 주문 10건 / 재고 3건 / 생산큐 3건)
python dummy_generator.py

# 개수 직접 지정
python dummy_generator.py --samples 8 --orders 20 --inventories 5 --queue 4
```

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--samples` | 5 | 생성할 시료 수 (최대 8종) |
| `--orders` | 10 | 생성할 주문 수 |
| `--inventories` | 3 | 재고 레코드를 생성할 시료 수 |
| `--queue` | 3 | PRODUCING 상태로 생성할 주문 수 |

생성되는 데이터:

- **samples** — 실리콘·GaAs·SiC 웨이퍼 등 8종 중 무작위 선택
- **orders** — 삼성전자·SK하이닉스 등 실제 기업명 기반, 상태 자동 배분
- **inventories** — 일부 시료에만 재고 레코드 생성 (나머지는 재고 없음)
- **production_queue** — PRODUCING 주문에 대한 큐 레코드 자동 등록

---

## DB 모니터 (JSON 뷰어)

`db/db.json`의 내용을 Rich 기반 테이블로 실시간 조회할 수 있는 읽기 전용 REPL입니다.

```bash
# db/ 디렉토리로 이동 후 실행
cd db

# 기본 파일(db.json) 연결
python main.py

# 파일 직접 지정
python main.py path/to/custom.json
```

REPL 진입 후 컬렉션 이름을 입력하면 해당 컬렉션의 레코드를 테이블로 출력합니다.

```
> orders          # orders 컬렉션 조회
> samples         # samples 컬렉션 조회
> exit            # 종료
```

---

## 테스트

```bash
# 전체 테스트 실행
pytest

# 파일 단위 실행
pytest tests/test_order.py

# 단일 케이스 실행
pytest tests/test_order.py::test_reserve_order

# 첫 번째 실패에서 중단
pytest -x

# 상세 출력
pytest -v
```

---

## 프로젝트 구조

```
SampleOrderSystem/
├── main.py                  # 진입점
├── app.py                   # MVC 조립 (create_app)
├── controllers/             # 사용자 입력 처리 → Model 조작
├── models/                  # 도메인 로직 + Observer 이벤트 발행
├── views/                   # 화면 렌더링 + 사용자 입력 수집
├── db/
│   ├── db.json              # JSON 데이터 파일
│   ├── json_store.py        # CRUD 영속성 레이어
│   ├── dummy_generator.py   # 더미 데이터 생성기
│   └── main.py              # DB 모니터 진입점
└── tests/                   # pytest 테스트
```

---

## Windows 한글 출력 문제

터미널에서 한글이 깨질 경우 실행 전 코드 페이지를 UTF-8로 변경합니다.

```bat
chcp 65001
python main.py
```

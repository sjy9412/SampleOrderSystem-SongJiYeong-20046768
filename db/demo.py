"""
CRUD 동작 확인용 데모 스크립트
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import json_store as store


def divider(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print('─' * 50)


def pp(label: str, value) -> None:
    import json
    print(f"\n[{label}]")
    print(json.dumps(value, ensure_ascii=False, indent=2))


# ── 준비: 컬렉션 초기화 ─────────────────────────────────────────────────────────
store.reset("users")
store.reset("posts")

# ── Create ──────────────────────────────────────────────────────────────────────
divider("CREATE")

alice = store.create("users", {"name": "Alice", "email": "alice@example.com", "role": "admin"})
bob   = store.create("users", {"name": "Bob",   "email": "bob@example.com",   "role": "user"})
carol = store.create("users", {"name": "Carol", "email": "carol@example.com", "role": "user"})

pp("Alice", alice)
pp("Bob", bob)
pp("Carol", carol)

post1 = store.create("posts", {"title": "Hello World", "body": "첫 번째 포스트입니다.", "author_id": alice["id"]})
post2 = store.create("posts", {"title": "JSON 영속성", "body": "파일로 데이터를 저장합니다.", "author_id": bob["id"]})

pp("Post 1", post1)
pp("Post 2", post2)

# ── Read All ────────────────────────────────────────────────────────────────────
divider("READ ALL")

all_users = store.read_all("users")
print(f"\n전체 사용자 수: {len(all_users)}")
for u in all_users:
    print(f"  - {u['name']} ({u['email']}) [{u['role']}]")

# ── Read with filter ────────────────────────────────────────────────────────────
divider("READ (role=user 필터)")

regular_users = store.read_all("users", role="user")
print(f"\nrole=user 사용자 수: {len(regular_users)}")
for u in regular_users:
    print(f"  - {u['name']}")

# ── Read One ────────────────────────────────────────────────────────────────────
divider("READ ONE")

found = store.read_one("users", alice["id"])
pp(f"ID로 조회: {alice['id'][:8]}…", found)

not_found = store.read_one("users", "nonexistent-id")
print(f"\n없는 ID 조회 결과: {not_found}")

# ── Update ──────────────────────────────────────────────────────────────────────
divider("UPDATE")

updated_bob = store.update("users", bob["id"], {"role": "moderator", "email": "bob-new@example.com"})
pp("Bob 업데이트 후", updated_bob)

# updated_at 변경 확인
print(f"\ncreated_at : {bob['created_at']}")
print(f"updated_at : {updated_bob['updated_at']}")
print(f"변경됨: {bob['created_at'] != updated_bob['updated_at']}")

# ── Delete ──────────────────────────────────────────────────────────────────────
divider("DELETE")

deleted = store.delete("users", carol["id"])
print(f"\nCarol 삭제 성공: {deleted}")
print(f"삭제 후 사용자 수: {len(store.read_all('users'))}")

double_delete = store.delete("users", carol["id"])
print(f"이미 삭제된 항목 재삭제 시도: {double_delete}")

# ── 최종 상태 확인 ───────────────────────────────────────────────────────────────
divider("최종 상태 (db.json 내용)")

import json, os
with open(os.path.join(os.path.dirname(__file__), "db.json"), encoding="utf-8") as f:
    print(f.read())

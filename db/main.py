"""DataMonitor — 진입점."""
import os
import sys

if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from monitor.repl import run

if __name__ == "__main__":
    db = sys.argv[1] if len(sys.argv) > 1 else "db.json"
    run(db)

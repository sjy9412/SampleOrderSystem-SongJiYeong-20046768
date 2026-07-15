import sys
import io

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stdin  = io.TextIOWrapper(sys.stdin.buffer,  encoding="utf-8")

    view_type = sys.argv[1] if len(sys.argv) > 1 else "table"
    from app import create_app
    create_app(view_type).run()

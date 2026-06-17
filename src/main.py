import sys

from screen import APISandbox


def main() -> int:
    app = APISandbox()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

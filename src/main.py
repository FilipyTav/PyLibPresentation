import sys
from textual.app import App, ComposeResult
from textual.widgets import (
    Button,
)


class APISandbox(App):
    CSS = """
    #request-bar { height: 3; dock: top; }
    #main-content { margin: 1; }
    #url-input { width: 1fr; }
    """

    BINDINGS = [("q", "quit", "Sair")]

    def compose(self) -> ComposeResult:
        pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        pass


def main() -> int:
    app = APISandbox()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

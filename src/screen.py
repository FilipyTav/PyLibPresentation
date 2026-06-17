import httpx
import json
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Header,
    Footer,
    Button,
    Input,
    TabbedContent,
    TabPane,
    TextArea,
)


class APISandbox(App):
    CSS = """
    #request-bar { height: 3; dock: top; }
    #main-content { margin: 1; }
    #url-input { width: 1fr; }
    """

    BINDINGS = [("q", "quit", "Sair")]

    def compose(self) -> ComposeResult:
        yield Header()

        yield Horizontal(
            Input(value="https://jsonplaceholder.typicode.com/posts/1", id="url-input"),
            Button("Executar", id="run-btn", variant="primary"),
            id="request-bar",
        )

        with TabbedContent(id="response-tabs"):
            yield TabPane("Resposta", id="tab-response")
            yield TabPane("Headers", id="tab-headers")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            url = self.query_one("#url-input", Input).value
            response_pane = self.query_one("#tab-response", TabPane)

            for child in response_pane.children:
                await child.remove()

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)

                    pretty_json = json.dumps(response.json(), indent=4)

                    await response_pane.mount(TextArea(pretty_json, read_only=True))

            except Exception as e:
                await response_pane.mount(
                    TextArea(f"Erro ao conectar: {str(e)}", read_only=True)
                )

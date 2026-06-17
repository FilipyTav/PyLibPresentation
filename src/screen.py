import sys
import httpx
import json
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    Button,
    Input,
    TabbedContent,
    TabPane,
    TextArea,
    LoadingIndicator,
    Select,
)


class APISandbox(App):
    CSS = """
    HeaderIcon {
        display: none;
    }

    #request-bar {
        height: auto;
        padding: 1 2;
        background: $surface;
        border-bottom: solid $panel;
    }
    
    /* Estilização para o seletor de métodos */
    #method-select {
        width: 16;
        margin-right: 1;
    }
    
    #url-input {
        width: 1fr;
        border: tall $primary;
        margin-right: 1;
    }
    
    #url-input:focus {
        border: tall $accent;
    }
    
    #run-btn {
        width: 16;
        text-style: bold;
    }

    #main-container {
        padding: 1 2;
    }

    TabbedContent {
        margin-top: 1;
    }

    TabPane {
        padding: 1;
        background: $surface;
    }

    TextArea {
        border: solid $panel;
        height: 1fr;
    }
    
    .error-text {
        color: $error;
        background: $error-darken-2;
        border: solid $error;
    }
    """

    BINDINGS = [("q", "quit", "Sair")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        http_methods = [
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
        ]

        yield Horizontal(
            Select(
                options=http_methods,
                value="GET",
                allow_blank=False,
                id="method-select",
            ),
            Input(
                value="https://jsonplaceholder.typicode.com/posts/1",
                id="url-input",
                placeholder="Insira a URL da API...",
            ),
            Button("Enviar", id="run-btn", variant="success"),
            id="request-bar",
        )

        with Vertical(id="main-container"):
            with TabbedContent(id="response-tabs"):
                with TabPane("JSON Resposta", id="tab-response"):
                    yield TextArea(
                        "// Os resultados da API aparecerão aqui...",
                        language="json",
                        read_only=True,
                    )
                with TabPane("Headers", id="tab-headers"):
                    yield TextArea(
                        "// Aguardando requisição...", language="json", read_only=True
                    )

        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        try:
            pass
        except Exception:
            pass

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            url = self.query_one("#url-input", Input).value

            select_value = self.query_one("#method-select", Select).value

            if select_value is None or select_value == Select.BLANK:
                method = "GET"
            else:
                method = str(select_value)

            response_pane = self.query_one("#tab-response", TabPane)
            headers_pane = self.query_one("#tab-headers", TabPane)
            button = event.button

            button.disabled = True
            response_pane.query("*").remove()
            headers_pane.query("*").remove()

            await response_pane.mount(LoadingIndicator())
            await headers_pane.mount(LoadingIndicator())

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url)

                    response_pane.query(LoadingIndicator).remove()
                    headers_pane.query(LoadingIndicator).remove()

                    try:
                        pretty_json = json.dumps(response.json(), indent=4)
                    except json.JSONDecodeError:
                        pretty_json = response.text

                    await response_pane.mount(
                        TextArea(pretty_json, language="json", read_only=True)
                    )

                    pretty_headers = json.dumps(dict(response.headers), indent=4)
                    await headers_pane.mount(
                        TextArea(pretty_headers, language="json", read_only=True)
                    )

            except Exception as e:
                response_pane.query(LoadingIndicator).remove()
                headers_pane.query(LoadingIndicator).remove()

                error_area = TextArea(f"Erro ao conectar:\n\n{str(e)}", read_only=True)
                error_area.add_class("error-text")
                await response_pane.mount(error_area)

            finally:
                button.disabled = False

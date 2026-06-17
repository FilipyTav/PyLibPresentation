import httpx
import json
from textual import on
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
    Label,
    ListView,
    ListItem,
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

    #workspace {
        height: 1fr;
    }

    #sidebar {
        width: 36;
        background: $surface-darken-1;
        border-right: solid $panel;
        padding: 1;
    }

    #sidebar-title {
        text-style: bold;
        margin-bottom: 1;
        content-align: center middle;
        color: $accent;
    }

    #main-container {
        width: 1fr;
        padding: 1 2;
    }

    #status-display {
        background: $panel;
        padding: 0 2;
        margin-top: 1;
        height: 1;
        text-style: bold;
        content-align: center middle;
        display: none;
    }

    #status-display.success-status {
        color: $success;
    }

    #status-display.error-status {
        color: $error;
    }

    TabbedContent {
        margin-top: 1;
    }

    TabPane {
        padding: 1;
        background: $surface;
    }

    TextArea, #history-list {
        border: solid $panel;
        height: 1fr;
    }

    /* Espaçamento vertical entre os blocos de histórico */
    #history-list ListItem {
        margin-bottom: 1;
        padding: 0 1;
        height: auto;
    }
    
    .error-text {
        color: $error;
        background: $error-darken-2;
        border: solid $error;
    }
    """

    BINDINGS = [("q", "quit", "Sair"), ("h", "toggle_sidebar", "Histórico")]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.request_history = []
        self._active_notification = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        http_methods = [
            ("GET", "GET"),
            ("POST", "POST"),
            ("PUT", "PUT"),
            ("DELETE", "DELETE"),
            ("PATCH", "PATCH"),
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

        with Horizontal(id="workspace"):
            with Vertical(id="sidebar"):
                yield Label("HISTÓRICO", id="sidebar-title")
                yield ListView(id="history-list")

            with Vertical(id="main-container"):
                yield Label("", id="status-display")

                with TabbedContent(id="response-tabs"):
                    with TabPane("Resposta", id="tab-response"):
                        yield TextArea(
                            "Os resultados da API aparecerão aqui...",
                            language="json",
                            read_only=True,
                        )
                    with TabPane("Request Body", id="tab-request-body"):
                        yield TextArea(
                            '{\n    "title": "foo",\n    "body": "bar",\n    "userId": 1\n}',
                            language="json",
                            read_only=False,
                        )
                    with TabPane("Headers", id="tab-headers"):
                        yield TextArea(
                            "Aguardando requisição...",
                            language="json",
                            read_only=True,
                        )

        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        try:
            pass
        except Exception:
            pass

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display

    @on(ListView.Selected, "#history-list")
    def handle_history_selection(self, event: ListView.Selected) -> None:
        index = event.index
        if index is not None and 0 <= index < len(self.request_history):
            saved_data = self.request_history[index]
            self.query_one("#url-input", Input).value = saved_data["url"]
            self.query_one("#method-select", Select).value = saved_data["method"]
            self.query_one("#tab-request-body", TabPane).query_one(
                TextArea
            ).text = saved_data["body"]

            if self._active_notification:
                try:
                    self._active_notification.dismiss()
                except Exception:
                    pass

            self._active_notification = self.notify(
                "Requisição restaurada!",
                title="Histórico",
                severity="information",
                timeout=1.5,
            )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-btn":
            url = self.query_one("#url-input", Input).value
            select_value = self.query_one("#method-select", Select).value

            if select_value is None or select_value == Select.BLANK:
                method = "GET"
            else:
                method = str(select_value)

            status_display = self.query_one("#status-display", Label)
            response_pane = self.query_one("#tab-response", TabPane)
            headers_pane = self.query_one("#tab-headers", TabPane)
            history_list = self.query_one("#history-list", ListView)
            button = event.button

            button.disabled = True
            status_display.display = False

            status_display.remove_class("success-status", "error-status")

            response_pane.query("*").remove()
            headers_pane.query("*").remove()

            await response_pane.mount(LoadingIndicator())
            await headers_pane.mount(LoadingIndicator())

            request_body_area = self.query_one("#tab-request-body", TabPane).query_one(
                TextArea
            )
            raw_body = request_body_area.text

            payload_data = None
            if method in ("POST", "PUT", "PATCH") and raw_body.strip():
                try:
                    payload_data = json.loads(raw_body)
                except json.JSONDecodeError:
                    payload_data = raw_body

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url, json=payload_data)

                    self.request_history.append(
                        {"method": method, "url": url, "body": raw_body}
                    )
                    
                    display_url = url
                    if len(display_url) > 30:
                        display_url = display_url[:27] + "..."
                    
                    entry_text = f"{method} [{response.status_code}]\n{display_url}"
                    await history_list.append(ListItem(Label(entry_text)))

                    response_pane.query(LoadingIndicator).remove()
                    headers_pane.query(LoadingIndicator).remove()

                    status_display.display = True
                    status_display.update(
                        f"Status: {response.status_code} {response.reason_phrase}"
                    )

                    if response.is_success:
                        status_display.add_class("success-status")
                    else:
                        status_display.add_class("error-status")

                    content_type = response.headers.get("content-type", "").lower()

                    display_text = ""
                    syntax_language = "json"

                    if "image/" in content_type:
                        size_kb = len(response.content) / 1024
                        display_text = (
                            f"TIPO: Imagem Detectada\n"
                            f"CONTENT-TYPE: {content_type}\n"
                            f"TAMANHO: {size_kb:.2f} KB\n\n"
                            f"Nota: Interfaces de terminal não exibem arquivos binários diretamente."
                        )
                        syntax_language = "json"

                    elif "text/html" in content_type:
                        display_text = f"\n{response.text}"
                        syntax_language = "html"

                    else:
                        try:
                            parsed_json = response.json()
                            display_text = json.dumps(parsed_json, indent=4)
                            syntax_language = "json"
                        except json.JSONDecodeError:
                            display_text = response.text
                            syntax_language = "json"

                    await response_pane.mount(
                        TextArea(display_text, language=syntax_language, read_only=True)
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

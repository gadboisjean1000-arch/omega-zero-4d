"""Serveur HTTP 100 % stdlib (0$ PMU) pour Google Cloud Run et sas Agent Ready."""

from __future__ import annotations

import importlib.util
import json
import os
import signal
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from .supela_agent_ready_engine import SupelaAgentRuntime

MAX_BODY_BYTES = 65_536


def _load_engine() -> ModuleType:
    """Charge le moteur local sans déclencher __init__.py (zéro dépendance externe)."""
    if __package__:
        from . import supela_agent_ready_engine

        return supela_agent_ready_engine

    module_name = "_supela_agent_ready_engine"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing

    engine_path = Path(__file__).with_name("supela_agent_ready_engine.py")
    spec = importlib.util.spec_from_file_location(module_name, engine_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Impossible de charger le moteur Agent Ready : {engine_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _reject_json_constant(token: str) -> Any:
    raise ValueError(f"Constante JSON non standard refusée : {token}")


class SupelaHttpServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    runtime: Any


def _make_handler(runtime: Any) -> type[BaseHTTPRequestHandler]:
    class SupelaAgentRequestHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
            raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(raw)

        def _read_json_body(self) -> tuple[dict[str, Any] | None, tuple[HTTPStatus, dict[str, Any]] | None]:
            raw_len = self.headers.get("Content-Length")
            if raw_len is None:
                return None, (
                    HTTPStatus.BAD_REQUEST,
                    {
                        "state": [0, 0, 0, 0],
                        "admitted": False,
                        "result": {"error": "Payload JSON invalide (RESET_PI0)"},
                        "doctrine": "0$ PMU",
                    },
                )
            try:
                content_length = int(raw_len)
            except ValueError:
                return None, (
                    HTTPStatus.BAD_REQUEST,
                    {
                        "state": [0, 0, 0, 0],
                        "admitted": False,
                        "result": {"error": "En-tête Content-Length invalide (RESET_PI0)"},
                        "doctrine": "0$ PMU",
                    },
                )
            if content_length < 0:
                return None, (
                    HTTPStatus.BAD_REQUEST,
                    {
                        "state": [0, 0, 0, 0],
                        "admitted": False,
                        "result": {"error": "En-tête Content-Length négatif (RESET_PI0)"},
                        "doctrine": "0$ PMU",
                    },
                )
            if content_length > MAX_BODY_BYTES:
                return None, (
                    HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    {
                        "state": [0, 0, 0, 0],
                        "admitted": False,
                        "result": {"error": "Payload trop volumineux (RESET_PI0)"},
                        "doctrine": "0$ PMU",
                    },
                )

            raw_body = self.rfile.read(content_length) if content_length > 0 else b""
            try:
                decoded = raw_body.decode("utf-8")
                parsed = json.loads(decoded, parse_constant=_reject_json_constant)
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
                return None, (
                    HTTPStatus.BAD_REQUEST,
                    {
                        "state": [0, 0, 0, 0],
                        "admitted": False,
                        "result": {"error": "Payload JSON invalide (RESET_PI0)"},
                        "doctrine": "0$ PMU",
                    },
                )
            if not isinstance(parsed, dict):
                return None, (
                    HTTPStatus.BAD_REQUEST,
                    {
                        "state": [0, 0, 0, 0],
                        "admitted": False,
                        "result": {"error": "Payload JSON invalide (RESET_PI0)"},
                        "doctrine": "0$ PMU",
                    },
                )
            return parsed, None

        def _handle_verify(self) -> None:
            payload, error_response = self._read_json_body()
            if error_response is not None or payload is None:
                assert error_response is not None
                self._send_json(error_response[0], error_response[1])
                return

            tool_name = payload.get("tool_name", "")
            arguments = payload.get("arguments", {})
            active_scope = payload.get("active_scope", "")

            state, result = runtime.execute_agent_call(tool_name, arguments, active_scope)
            admitted = state == (1, 1, 1, 1)
            if admitted:
                status = HTTPStatus.OK
            else:
                error_msg = str(result.get("error", ""))
                if "DENY_INVALID_ARGS" in error_msg:
                    status = HTTPStatus.BAD_REQUEST
                elif "DENY_UNKNOWN_TOOL" in error_msg or "DENY_SCOPE" in error_msg:
                    status = HTTPStatus.FORBIDDEN
                else:
                    status = HTTPStatus.INTERNAL_SERVER_ERROR

            latest_proof = runtime.audit_worm_log[-1] if runtime.audit_worm_log else None
            self._send_json(
                status,
                {
                    "state": list(state),
                    "admitted": admitted,
                    "result": result,
                    "proof_hash": latest_proof.proof_hash if latest_proof else "",
                    "worm_chain_valid": runtime.verify_worm_chain(),
                    "doctrine": "0$ PMU",
                },
            )

        def _method_not_allowed(self) -> None:
            self._send_json(
                HTTPStatus.METHOD_NOT_ALLOWED,
                {
                    "state": [0, 0, 0, 0],
                    "admitted": False,
                    "error": "METHOD_NOT_ALLOWED",
                    "doctrine": "0$ PMU",
                },
            )

        def _not_found(self) -> None:
            self._send_json(
                HTTPStatus.NOT_FOUND,
                {
                    "state": [0, 0, 0, 0],
                    "admitted": False,
                    "error": "NOT_FOUND",
                    "doctrine": "0$ PMU",
                },
            )

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/healthz":
                self._send_json(HTTPStatus.OK, {"status": "ALIVE", "doctrine": "0$ PMU"})
                return
            if path == "/verify":
                self._method_not_allowed()
                return
            self._not_found()

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path == "/verify":
                self._handle_verify()
                return
            if path == "/healthz":
                self._method_not_allowed()
                return
            self._not_found()

        def do_PUT(self) -> None:
            self._method_not_allowed()

        def do_DELETE(self) -> None:
            self._method_not_allowed()

        def do_PATCH(self) -> None:
            self._method_not_allowed()

        def do_OPTIONS(self) -> None:
            self._method_not_allowed()

    return SupelaAgentRequestHandler


def create_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    runtime: SupelaAgentRuntime | None = None,
) -> SupelaHttpServer:
    """Instancie le serveur HTTP stdlib Cloud Run (0$ PMU)."""
    if runtime is None:
        engine = _load_engine()
        active_runtime: Any = engine.build_default_runtime()
    else:
        active_runtime = runtime

    server = SupelaHttpServer((host, port), _make_handler(active_runtime))
    server.runtime = active_runtime
    return server


def main() -> int:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    server = create_server(host=host, port=port)
    bound_port = server.server_address[1]

    def _request_shutdown(_signum: int, _frame: Any) -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    if threading.current_thread() is threading.main_thread():
        for sig_name in ("SIGINT", "SIGTERM"):
            sig = getattr(signal, sig_name, None)
            if sig is not None:
                signal.signal(sig, _request_shutdown)

    print(
        json.dumps(
            {
                "status": "LISTENING",
                "host": host,
                "port": bound_port,
                "doctrine": "0$ PMU",
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

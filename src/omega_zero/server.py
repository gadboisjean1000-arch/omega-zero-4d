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
REQUEST_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_WORKERS = 32


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

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[BaseHTTPRequestHandler],
        *,
        max_workers: int = DEFAULT_MAX_WORKERS,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers doit être >= 1.")
        self._worker_slots = threading.BoundedSemaphore(max_workers)
        super().__init__(server_address, request_handler_class)

    def process_request(self, request: Any, client_address: Any) -> None:
        if not self._worker_slots.acquire(blocking=False):
            self.shutdown_request(request)
            return

        def _worker() -> None:
            try:
                self.process_request_thread(request, client_address)
            finally:
                self._worker_slots.release()

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()


def _make_handler(
    runtime: Any,
    allowed_scopes: frozenset[str] | None,
) -> type[BaseHTTPRequestHandler]:
    class SupelaAgentRequestHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"
        timeout = REQUEST_TIMEOUT_SECONDS

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _send_json(
            self,
            status: HTTPStatus,
            payload: dict[str, Any],
            extra_headers: dict[str, str] | None = None,
        ) -> None:
            raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.close_connection = True
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Connection", "close")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if extra_headers:
                for key, value in extra_headers.items():
                    self.send_header(key, value)
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

            if allowed_scopes is not None and (
                not isinstance(active_scope, str) or active_scope not in allowed_scopes
            ):
                self._send_json(
                    HTTPStatus.FORBIDDEN,
                    {
                        "state": [0, 0, 0, 0],
                        "admitted": False,
                        "result": {
                            "error": f"Périmètre '{active_scope}' refusé par la politique serveur (DENY_SCOPE)"
                        },
                        "instance_id": runtime.instance_id,
                        "persistence": "EPHEMERAL_INSTANCE_MEMORY",
                        "doctrine": "0$ PMU",
                    },
                )
                return

            receipt = runtime.execute_agent_call_with_proof(tool_name, arguments, active_scope)
            admitted = receipt.state == (1, 1, 1, 1)
            if admitted:
                status = HTTPStatus.OK
            else:
                error_msg = str(receipt.result.get("error", ""))
                if "DENY_INVALID_ARGS" in error_msg:
                    status = HTTPStatus.BAD_REQUEST
                elif "DENY_UNKNOWN_TOOL" in error_msg or "DENY_SCOPE" in error_msg:
                    status = HTTPStatus.FORBIDDEN
                elif "CONTRACT_PI0" in error_msg:
                    status = HTTPStatus.UNPROCESSABLE_ENTITY
                else:
                    status = HTTPStatus.INTERNAL_SERVER_ERROR

            self._send_json(
                status,
                {
                    "state": list(receipt.state),
                    "admitted": admitted,
                    "result": receipt.result,
                    "proof_hash": receipt.proof.proof_hash,
                    "prev_proof_hash": receipt.proof.prev_proof_hash,
                    "worm_link_verified": receipt.worm_link_verified,
                    "chain_length": receipt.chain_length,
                    "instance_id": runtime.instance_id,
                    "persistence": "EPHEMERAL_INSTANCE_MEMORY",
                    "doctrine": "0$ PMU",
                },
            )

        def _method_not_allowed(self, allow: str) -> None:
            self._send_json(
                HTTPStatus.METHOD_NOT_ALLOWED,
                {
                    "state": [0, 0, 0, 0],
                    "admitted": False,
                    "error": "METHOD_NOT_ALLOWED",
                    "doctrine": "0$ PMU",
                },
                extra_headers={"Allow": allow},
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
                self._method_not_allowed("POST")
                return
            self._not_found()

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path == "/verify":
                self._handle_verify()
                return
            if path == "/healthz":
                self._method_not_allowed("GET")
                return
            self._not_found()

        def _handle_disallowed_method(self) -> None:
            path = urlparse(self.path).path
            if path == "/healthz":
                self._method_not_allowed("GET")
                return
            if path == "/verify":
                self._method_not_allowed("POST")
                return
            self._not_found()

        def do_PUT(self) -> None:
            self._handle_disallowed_method()

        def do_DELETE(self) -> None:
            self._handle_disallowed_method()

        def do_PATCH(self) -> None:
            self._handle_disallowed_method()

        def do_OPTIONS(self) -> None:
            self._handle_disallowed_method()

    return SupelaAgentRequestHandler


def create_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    runtime: SupelaAgentRuntime | None = None,
    *,
    allowed_scopes: frozenset[str] | None = None,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> SupelaHttpServer:
    """Instancie le serveur HTTP stdlib Cloud Run (0$ PMU)."""
    if runtime is None:
        engine = _load_engine()
        active_runtime: Any = engine.build_default_runtime()
    else:
        active_runtime = runtime

    resolved_scopes = allowed_scopes
    if resolved_scopes is None:
        raw_scopes = os.environ.get("SUPELA_ALLOWED_SCOPES", "")
        parsed = frozenset(s.strip() for s in raw_scopes.split(",") if s.strip())
        resolved_scopes = parsed if parsed else None

    server = SupelaHttpServer(
        (host, port),
        _make_handler(active_runtime, resolved_scopes),
        max_workers=max_workers,
    )
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
                "instance_id": server.runtime.instance_id,
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

"""Tests du serveur HTTP Cloud Run 100 % Python stdlib (0$ PMU)."""

from __future__ import annotations

import hashlib
import json
import os
import queue
import socket
import subprocess
import sys
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from omega_zero.server import SupelaHttpServer, create_server


def _http_request(
    url: str,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], dict[str, Any]]:
    req = Request(url=url, data=body, method=method, headers=headers or {})
    try:
        with urlopen(req, timeout=5.0) as resp:
            raw = resp.read().decode("utf-8")
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, resp_headers, json.loads(raw)
    except HTTPError as err:
        raw = err.read().decode("utf-8")
        resp_headers = {k.lower(): v for k, v in err.headers.items()}
        return err.code, resp_headers, json.loads(raw)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture()
def live_server() -> Iterator[tuple[str, SupelaHttpServer]]:
    server = create_server(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[0], server.server_address[1]
    base_url = f"http://{host}:{port}"
    try:
        yield base_url, server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_healthz_returns_alive(live_server: tuple[str, SupelaHttpServer]) -> None:
    base_url, _ = live_server
    status, headers, data = _http_request(f"{base_url}/healthz")
    assert status == 200
    assert data == {"status": "ALIVE", "doctrine": "0$ PMU"}
    assert headers.get("connection") == "close"
    assert headers.get("cache-control") == "no-store"
    assert headers.get("x-content-type-options") == "nosniff"


def test_verify_admitted_execution(live_server: tuple[str, SupelaHttpServer]) -> None:
    base_url, server = live_server
    payload = json.dumps(
        {
            "tool_name": "local_sha256",
            "arguments": {"data": "supela-cloudrun"},
            "active_scope": "research",
        }
    ).encode("utf-8")
    status, headers, data = _http_request(
        f"{base_url}/verify",
        method="POST",
        body=payload,
        headers={"Content-Type": "application/json"},
    )
    assert status == 200
    assert headers.get("connection") == "close"
    assert data["state"] == [1, 1, 1, 1]
    assert data["admitted"] is True
    assert data["worm_link_verified"] is True
    assert data["chain_length"] == 1
    assert data["instance_id"] == server.runtime.instance_id
    assert data["persistence"] == "EPHEMERAL_INSTANCE_MEMORY"
    assert isinstance(data["proof_hash"], str) and len(data["proof_hash"]) == 64
    assert "digest" in data["result"]


def test_verify_pi0_check_contracts_empty_state(live_server: tuple[str, SupelaHttpServer]) -> None:
    base_url, _ = live_server
    payload = json.dumps(
        {
            "tool_name": "pi0_check",
            "arguments": {},
            "active_scope": "audit",
        }
    ).encode("utf-8")
    status, headers, data = _http_request(
        f"{base_url}/verify",
        method="POST",
        body=payload,
        headers={"Content-Type": "application/json"},
    )
    assert status == 422
    assert headers.get("connection") == "close"
    assert data["state"] == [0, 0, 0, 0]
    assert data["admitted"] is False
    assert data["worm_link_verified"] is True
    assert "CONTRACT_PI0" in data["result"]["error"]


def test_verify_scope_violation_returns_403_pi0(live_server: tuple[str, SupelaHttpServer]) -> None:
    base_url, _ = live_server
    payload = json.dumps(
        {
            "tool_name": "local_sha256",
            "arguments": {"data": "forbidden"},
            "active_scope": "public_untrusted",
        }
    ).encode("utf-8")
    status, headers, data = _http_request(
        f"{base_url}/verify",
        method="POST",
        body=payload,
        headers={"Content-Type": "application/json"},
    )
    assert status == 403
    assert headers.get("connection") == "close"
    assert data["state"] == [0, 0, 0, 0]
    assert data["admitted"] is False
    assert "DENY_SCOPE" in data["result"]["error"]


def test_verify_unknown_tool_returns_403_pi0(live_server: tuple[str, SupelaHttpServer]) -> None:
    base_url, _ = live_server
    payload = json.dumps(
        {
            "tool_name": "rm_rf",
            "arguments": {"path": "/"},
            "active_scope": "audit",
        }
    ).encode("utf-8")
    status, headers, data = _http_request(
        f"{base_url}/verify",
        method="POST",
        body=payload,
        headers={"Content-Type": "application/json"},
    )
    assert status == 403
    assert headers.get("connection") == "close"
    assert data["state"] == [0, 0, 0, 0]
    assert data["admitted"] is False
    assert "DENY_UNKNOWN_TOOL" in data["result"]["error"]


def test_verify_malformed_json_returns_400(live_server: tuple[str, SupelaHttpServer]) -> None:
    base_url, _ = live_server
    status, headers, data = _http_request(
        f"{base_url}/verify",
        method="POST",
        body=b"{not-json",
        headers={"Content-Type": "application/json"},
    )
    assert status == 400
    assert headers.get("connection") == "close"
    assert data["state"] == [0, 0, 0, 0]
    assert data["admitted"] is False
    assert "RESET_PI0" in data["result"]["error"]


def test_verify_oversized_body_returns_413_and_closes(live_server: tuple[str, SupelaHttpServer]) -> None:
    base_url, _ = live_server
    oversized = b'{"data":"' + (b"a" * 70_000) + b'"}'
    status, headers, data = _http_request(
        f"{base_url}/verify",
        method="POST",
        body=oversized,
        headers={"Content-Type": "application/json"},
    )
    assert status == 413
    assert headers.get("connection") == "close"
    assert data["state"] == [0, 0, 0, 0]
    assert data["admitted"] is False

    # Vérifie que le serveur reste parfaitement sain après le rejet 413
    health_status, _, health_data = _http_request(f"{base_url}/healthz")
    assert health_status == 200
    assert health_data["status"] == "ALIVE"


def test_unknown_route_and_disallowed_methods(live_server: tuple[str, SupelaHttpServer]) -> None:
    base_url, _ = live_server
    status_404, headers_404, data_404 = _http_request(f"{base_url}/does-not-exist")
    assert status_404 == 404
    assert headers_404.get("connection") == "close"
    assert data_404["state"] == [0, 0, 0, 0]
    assert data_404["error"] == "NOT_FOUND"

    status_405_verify, headers_405_verify, data_405_verify = _http_request(
        f"{base_url}/verify", method="GET"
    )
    assert status_405_verify == 405
    assert headers_405_verify.get("connection") == "close"
    assert headers_405_verify.get("allow") == "POST"
    assert data_405_verify["state"] == [0, 0, 0, 0]
    assert data_405_verify["error"] == "METHOD_NOT_ALLOWED"

    status_405_health, headers_405_health, data_405_health = _http_request(
        f"{base_url}/healthz", method="POST", body=b"{}"
    )
    assert status_405_health == 405
    assert headers_405_health.get("connection") == "close"
    assert headers_405_health.get("allow") == "GET"
    assert data_405_health["error"] == "METHOD_NOT_ALLOWED"


def test_concurrent_verify_returns_exact_matching_proof(
    live_server: tuple[str, SupelaHttpServer],
) -> None:
    base_url, server = live_server

    def _call_one(idx: int) -> tuple[int, dict[str, Any]]:
        args = {"data": f"concurrent-item-{idx}"}
        body = json.dumps(
            {
                "tool_name": "local_sha256",
                "arguments": args,
                "active_scope": "verify",
            }
        ).encode("utf-8")
        status, _, resp = _http_request(
            f"{base_url}/verify",
            method="POST",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        assert status == 200
        return idx, resp

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(_call_one, range(16)))

    proofs_by_hash = {p.proof_hash: p for p in server.runtime.audit_worm_log}
    assert len(proofs_by_hash) == 16
    assert server.runtime.verify_worm_chain() is True

    for idx, resp in results:
        assert resp["state"] == [1, 1, 1, 1]
        assert resp["worm_link_verified"] is True
        proof = proofs_by_hash[resp["proof_hash"]]
        expected_args = json.dumps(
            {"data": f"concurrent-item-{idx}"},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        assert proof.arguments_hash == hashlib.sha256(expected_args).hexdigest()


def test_server_allowed_scopes_policy() -> None:
    server = create_server(host="127.0.0.1", port=0, allowed_scopes=frozenset({"verify"}))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{server.server_address[0]}:{server.server_address[1]}"
    try:
        denied_body = json.dumps(
            {
                "tool_name": "local_sha256",
                "arguments": {"data": "policy-test"},
                "active_scope": "research",
            }
        ).encode("utf-8")
        st_deny, _, deny_data = _http_request(
            f"{base_url}/verify",
            method="POST",
            body=denied_body,
            headers={"Content-Type": "application/json"},
        )
        assert st_deny == 403
        assert deny_data["state"] == [0, 0, 0, 0]
        assert "DENY_SCOPE" in deny_data["result"]["error"]

        ok_body = json.dumps(
            {
                "tool_name": "local_sha256",
                "arguments": {"data": "policy-test"},
                "active_scope": "verify",
            }
        ).encode("utf-8")
        st_ok, _, ok_data = _http_request(
            f"{base_url}/verify",
            method="POST",
            body=ok_body,
            headers={"Content-Type": "application/json"},
        )
        assert st_ok == 200
        assert ok_data["state"] == [1, 1, 1, 1]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2.0)


def test_standalone_subprocess_zero_dependency() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    server_script = repo_root / "src" / "omega_zero" / "server.py"
    free_port = _find_free_port()

    env = os.environ.copy()
    env["HOST"] = "127.0.0.1"
    env["PORT"] = str(free_port)
    env["PYTHONPATH"] = ""
    env["PYTHONUTF8"] = "1"

    # -S désactive site-packages : prouve mécaniquement le 0-dépendance tiers
    proc = subprocess.Popen(
        [sys.executable, "-S", str(server_script)],
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    try:
        assert proc.stdout is not None
        line_queue: queue.Queue[str] = queue.Queue()

        def _read_first_line() -> None:
            assert proc.stdout is not None
            line_queue.put(proc.stdout.readline().strip())

        reader = threading.Thread(target=_read_first_line, daemon=True)
        reader.start()
        try:
            startup_line = line_queue.get(timeout=5.0)
        except queue.Empty as exc:
            raise AssertionError(f"Timeout au démarrage de server.py (rc={proc.poll()})") from exc

        assert startup_line, f"Serveur non démarré (returncode={proc.poll()})"
        startup_info = json.loads(startup_line)
        assert startup_info["status"] == "LISTENING"
        assert startup_info["port"] == free_port
        assert startup_info["instance_id"]

        base_url = f"http://127.0.0.1:{free_port}"
        st_health, hdr_health, health_data = _http_request(f"{base_url}/healthz")
        assert st_health == 200
        assert hdr_health.get("connection") == "close"
        assert health_data == {"status": "ALIVE", "doctrine": "0$ PMU"}

        req_body = json.dumps(
            {
                "tool_name": "local_sha256",
                "arguments": {"data": "standalone"},
                "active_scope": "verify",
            }
        ).encode("utf-8")
        st_ok, _, ok_data = _http_request(
            f"{base_url}/verify",
            method="POST",
            body=req_body,
            headers={"Content-Type": "application/json"},
        )
        assert st_ok == 200
        assert ok_data["state"] == [1, 1, 1, 1]

        pi0_body = json.dumps(
            {
                "tool_name": "pi0_check",
                "arguments": {},
                "active_scope": "verify",
            }
        ).encode("utf-8")
        st_pi0, _, pi0_data = _http_request(
            f"{base_url}/verify",
            method="POST",
            body=pi0_body,
            headers={"Content-Type": "application/json"},
        )
        assert st_pi0 == 422
        assert pi0_data["state"] == [0, 0, 0, 0]

        bad_body = json.dumps(
            {
                "tool_name": "unknown_tool",
                "arguments": {},
                "active_scope": "verify",
            }
        ).encode("utf-8")
        st_deny, _, deny_data = _http_request(
            f"{base_url}/verify",
            method="POST",
            body=bad_body,
            headers={"Content-Type": "application/json"},
        )
        assert st_deny == 403
        assert deny_data["state"] == [0, 0, 0, 0]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5.0)

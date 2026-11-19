"""Adaptateur Serverless agnostique (Azure Functions Python v2 / local HTTP) pour Supela Is The Laws.

Conception 0 $ PMU / zéro dépendance propriétaire :
- N'importe aucune bibliothèque Azure obligatoire au runtime ;
- Strictement lecture seule (GET uniquement, 405 sur toute mutation) ;
- Compatible avec `microsoft/vscode-azurefunctions` (modèle Python v2) et tout serveur WSGI/ASGI/local.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .supela_laws import run_supela_laws_suite

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_LAWS_HTML_PATH = ROOT_DIR / "docs" / "constitution" / "LOIS_PROUVEES_SUPELA.html"


@dataclass(frozen=True)
class ServerlessHttpResponse:
    """Réponse HTTP portable (convertible en azure.functions.HttpResponse sans couplage fort)."""

    status_code: int
    body: str
    mimetype: str
    headers: dict[str, str]


def handle_supela_http_request(
    method: str,
    path: str,
    *,
    html_path: Path = DEFAULT_LAWS_HTML_PATH,
) -> ServerlessHttpResponse:
    """
    Routeur serverless fail-closed en lecture seule pour Supela Is The Laws :
      - GET /api/supela/health   -> état synthétique JSON
      - GET /api/supela/laws     -> manifeste complet des 12 lois + pyramide + topologie 4D
      - GET /api/supela/laws/web -> page web interactive HTML5 autonome (0 CDN)
    """
    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store",
    }

    if method.upper() != "GET":
        err = json.dumps(
            {
                "error": "METHOD_NOT_ALLOWED",
                "detail": "Surface serverless Supela strictement en lecture seule (GET uniquement).",
            },
            ensure_ascii=False,
        )
        return ServerlessHttpResponse(
            status_code=405,
            body=err,
            mimetype="application/json; charset=utf-8",
            headers={**security_headers, "Allow": "GET"},
        )

    normalized_path = "/" + path.strip("/")

    if normalized_path == "/api/supela/health":
        suite = run_supela_laws_suite()
        payload: dict[str, Any] = {
            "status": "OK",
            "schema": suite["schema"],
            "verdict_global": suite["verdict_global"],
            "laws_verified": suite["summary"]["laws_verified"],
            "laws_total": suite["summary"]["laws_total"],
            "digest_sha256": suite["digest_sha256"],
            "read_only_edge": True,
            "canonical_ledger_hosted_here": False,
        }
        return ServerlessHttpResponse(
            status_code=200,
            body=json.dumps(payload, indent=2, ensure_ascii=False),
            mimetype="application/json; charset=utf-8",
            headers=security_headers,
        )

    if normalized_path == "/api/supela/laws":
        suite = run_supela_laws_suite()
        return ServerlessHttpResponse(
            status_code=200,
            body=json.dumps(suite, indent=2, ensure_ascii=False),
            mimetype="application/json; charset=utf-8",
            headers=security_headers,
        )

    if normalized_path == "/api/supela/laws/web":
        if not html_path.is_file():
            err_body = json.dumps(
                {"error": "ARTIFACT_NOT_BUILT", "detail": "LOIS_PROUVEES_SUPELA.html introuvable."},
                ensure_ascii=False,
            )
            return ServerlessHttpResponse(
                status_code=503,
                body=err_body,
                mimetype="application/json; charset=utf-8",
                headers=security_headers,
            )
        return ServerlessHttpResponse(
            status_code=200,
            body=html_path.read_text(encoding="utf-8"),
            mimetype="text/html; charset=utf-8",
            headers=security_headers,
        )

    not_found = json.dumps(
        {"error": "NOT_FOUND", "path": normalized_path},
        ensure_ascii=False,
    )
    return ServerlessHttpResponse(
        status_code=404,
        body=not_found,
        mimetype="application/json; charset=utf-8",
        headers=security_headers,
    )

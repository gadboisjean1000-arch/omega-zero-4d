# Intégration Serverless Azure Functions (`microsoft/vscode-azurefunctions`) × Supela

> **Référence amont :** [`https://github.com/microsoft/vscode-azurefunctions`](https://github.com/microsoft/vscode-azurefunctions) (extension VS Code Azure Functions, licence `MIT`)  
> **Principe de souveraineté `0 $ PMU` :** Le cloud serverless est traité exclusivement comme une **surface périphérique de diffusion en lecture seule (`GET`)**. Le registre canonique, les preuves et les clés souveraines restent locaux et reproductibles hors ligne ; la disparition d'Azure ne détruit aucun état Supela.

---

## 1. Architecture Découplée (Zéro Verrouillage Fournisseur)

L'adaptateur portable [`src/omega_zero/serverless_laws_handler.py`](../../src/omega_zero/serverless_laws_handler.py) n'impose aucune dépendance Azure dans `pyproject.toml` et expose trois routes **fail-closed en lecture seule** (`405 Method Not Allowed` sur tout `POST`/`PUT`/`DELETE`, en-têtes `nosniff`, `DENY`, `no-referrer`, `no-store`) :

| Route HTTP | Méthode | Réponse | Rôle |
|---|---|---|---|
| `/api/supela/health` | `GET` | `200 application/json` | Sonde santé + verdict global + empreinte SHA-256 |
| `/api/supela/laws` | `GET` | `200 application/json` | Manifeste complet *Supela Is The Laws* (12 lois, pyramide internationale, topologie 4D & ISO 19115) |
| `/api/supela/laws/web` | `GET` | `200 text/html` | Page Web interactive autonome `LOIS_PROUVEES_SUPELA.html` (0 CDN) |

---

## 2. Branchement dans VS Code (`ms-azuretools.vscode-azurefunctions`)

Pour exposer l'adaptateur dans un projet Azure Functions Python v2 (géré via l'extension `microsoft/vscode-azurefunctions` + `Azure Functions Core Tools`) :

```python
import azure.functions as func
from omega_zero.serverless_laws_handler import handle_supela_http_request

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="supela/{*rest}", methods=["GET"])
def supela_laws_edge(req: func.HttpRequest) -> func.HttpResponse:
    route_tail = req.route_params.get("rest", "health")
    res = handle_supela_http_request(req.method, f"/api/supela/{route_tail}")
    return func.HttpResponse(
        body=res.body,
        status_code=res.status_code,
        mimetype=res.mimetype,
        headers=res.headers,
    )
```

---

## 3. Verrous de Sécurité Obligatoires (OIDC & Zéro Secret Statique)

1. **Zéro secret dans Git :** `local.settings.json` et toute chaîne de connexion Azure Storage doivent rester hors du dépôt (`.gitignore`).
2. **Déploiement sans secret statique :** utiliser **GitHub Actions OIDC (Federated Identity Credentials)** + Managed Identity (aligné sur le module Azure Bicep déjà inventorié dans l'encyclopédie Supela).
3. **Lecture seule absolue :** toute mutation, promotion ou ratification demeure interdite sur la surface serverless (`FourBoundaryGate` : `C ≠ P ≠ V ≠ A`, ratification souveraine humaine exclusive).

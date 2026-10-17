"""Accès exclusivement local au modèle de la maquette ; aucun fournisseur payant."""

from __future__ import annotations

import http.client
import json

LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 11435
LOCAL_MODEL = "qwen3:4b-instruct"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class LocalModelError(RuntimeError):
    """Le modèle local est absent, occupé ou a renvoyé une réponse inexploitable."""


def local_request(path: str, payload: dict, *, timeout: float = 180) -> dict:
    if path not in {"/api/show", "/api/chat"}:
        raise LocalModelError("Opération locale non autorisée.")
    # Adresse numérique fixe : ni URL distante, ni proxy, ni redirection HTTP.
    connection = http.client.HTTPConnection(LOCAL_HOST, LOCAL_PORT, timeout=timeout)
    try:
        connection.request("POST", path, json.dumps(payload).encode("utf-8"),
                           {"Content-Type": "application/json"})
        response = connection.getresponse()
        data = response.read(MAX_RESPONSE_BYTES + 1)
        if response.status != 200 or len(data) > MAX_RESPONSE_BYTES:
            raise LocalModelError("Le modèle local n'est pas prêt. Relance Lancer.command.")
        result = json.loads(data)
        if not isinstance(result, dict) or result.get("error"):
            raise LocalModelError("Réponse du moteur local inexploitable.")
        return result
    except LocalModelError:
        raise
    except (OSError, ValueError, http.client.HTTPException) as exc:
        raise LocalModelError("Le moteur local ne répond pas. Relance Lancer.command.") from exc
    finally:
        connection.close()


def require_local_model(*, timeout: float = 10) -> None:
    info = local_request("/api/show", {"model": LOCAL_MODEL}, timeout=timeout)
    if (info.get("remote_model") or info.get("remote_host")
            or info.get("details", {}).get("format") != "gguf"
            or not info.get("model_info")):
        raise LocalModelError("Le modèle doit être téléchargé et exécuté localement. Aucun modèle cloud n'est accepté.")


def model_status() -> tuple[bool, str]:
    try:
        require_local_model(timeout=1.5)
        return True, "Modèle local prêt · aucun frais d'API"
    except LocalModelError:
        return False, "Modèle local à démarrer avec Lancer.command"


def chat_local(messages: list[dict[str, str]]) -> str:
    require_local_model()
    result = local_request("/api/chat", {
        "model": LOCAL_MODEL, "messages": messages, "stream": False,
        "think": False, "keep_alive": "5m",
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 700},
    })
    text = result.get("message", {}).get("content", "")
    if not result.get("done") or result.get("done_reason") == "length" or not isinstance(text, str):
        raise LocalModelError("La synthèse locale est incomplète. Consulte les extraits.")
    return text.strip()

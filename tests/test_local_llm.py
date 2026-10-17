import json
from unittest.mock import Mock

import pytest

from memoire.local_llm import (
    LOCAL_MODEL,
    LocalModelError,
    chat_local,
    local_request,
    require_local_model,
)

LOCAL_INFO = {"details": {"format": "gguf"}, "model_info": {"general.architecture": "qwen3"}}


def test_transport_is_loopback_only_and_ignores_proxies(monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.example:8080")
    factory = Mock()
    connection = factory.return_value
    response = connection.getresponse.return_value
    response.status = 200
    response.read.return_value = b'{"ok": true}'
    monkeypatch.setattr("http.client.HTTPConnection", factory)
    assert local_request("/api/show", {"model": LOCAL_MODEL}) == {"ok": True}
    assert factory.call_args.args == ("127.0.0.1", 11435)
    args = connection.request.call_args.args
    assert args[:2] == ("POST", "/api/show")
    assert json.loads(args[2])["model"] == LOCAL_MODEL
    assert "Authorization" not in args[3]


def test_redirect_is_never_followed(monkeypatch):
    factory = Mock()
    factory.return_value.getresponse.return_value.status = 302
    factory.return_value.getresponse.return_value.read.return_value = b""
    monkeypatch.setattr("http.client.HTTPConnection", factory)
    with pytest.raises(LocalModelError):
        local_request("/api/chat", {})
    assert factory.call_count == 1


@pytest.mark.parametrize("metadata", [
    {**LOCAL_INFO, "remote_model": "paid-cloud"},
    {**LOCAL_INFO, "remote_host": "https://ollama.com"},
    {"details": {"format": "cloud"}, "model_info": {"name": "cloud"}},
    {"details": {"format": "gguf"}},
])
def test_cloud_or_non_local_model_is_refused(metadata, monkeypatch):
    request = Mock(return_value=metadata)
    monkeypatch.setattr("memoire.local_llm.local_request", request)
    with pytest.raises(LocalModelError):
        require_local_model()
    assert request.call_args.args[0] == "/api/show"


def test_generation_checks_local_weights_before_chat(monkeypatch):
    request = Mock(side_effect=[LOCAL_INFO, {"done": True, "message": {"content": "Inconnu. [S1]"}}])
    monkeypatch.setattr("memoire.local_llm.local_request", request)
    assert chat_local([{"role": "user", "content": "question"}]) == "Inconnu. [S1]"
    assert [call.args[0] for call in request.call_args_list] == ["/api/show", "/api/chat"]
    payload = request.call_args.args[1]
    assert payload["model"] == LOCAL_MODEL
    assert payload["stream"] is False


def test_incomplete_generation_is_not_presented_as_final(monkeypatch):
    request = Mock(side_effect=[LOCAL_INFO, {"done": True, "done_reason": "length",
                                           "message": {"content": "Début de réponse [S1]"}}])
    monkeypatch.setattr("memoire.local_llm.local_request", request)
    with pytest.raises(LocalModelError):
        chat_local([])

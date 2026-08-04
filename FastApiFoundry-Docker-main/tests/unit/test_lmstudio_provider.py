# -*- coding: utf-8 -*-

import pytest

from src.models.lmstudio_client import LMStudioClient, _extract_message_content
from src.models import router as model_router
from src.models.router import detect_backend


def test_detect_backend_lmstudio_prefix():
    assert detect_backend("lmstudio::ibm/granite-4-micro") == ("lmstudio", "ibm/granite-4-micro")


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("foundry::qwen3", ("foundry", "qwen3")),
        ("hf::Qwen/Qwen2.5", ("hf", "Qwen/Qwen2.5")),
        ("llama::D:/models/model.gguf", ("llama", "D:/models/model.gguf")),
        ("ollama::mistral", ("ollama", "mistral")),
    ],
)
def test_detect_backend_existing_prefixes_still_work(model, expected):
    assert detect_backend(model) == expected


def test_extract_message_content_joins_message_outputs_only():
    data = {
        "output": [
            {"type": "reasoning", "content": "hidden"},
            {"type": "message", "content": "Hello"},
            {"type": "tool_call", "output": "..."},
            {"type": "message", "content": " world"},
        ]
    }
    assert _extract_message_content(data) == "Hello world"


@pytest.mark.asyncio
async def test_lmstudio_client_list_models(monkeypatch):
    client = LMStudioClient()

    async def fake_request(method, path, **kwargs):
        assert method == "GET"
        assert path == "/api/v1/models"
        return 200, {"models": [{"key": "ibm/granite-4-micro"}]}

    monkeypatch.setattr(client, "_request", fake_request)
    result = await client.list_models()

    assert result["success"] is True
    assert result["count"] == 1
    assert result["models"][0]["key"] == "ibm/granite-4-micro"


@pytest.mark.asyncio
async def test_lmstudio_client_model_management(monkeypatch):
    client = LMStudioClient()
    calls = []

    async def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs.get("json")))
        if path == "/api/v1/models/load":
            return 200, {"type": "llm", "instance_id": "model-a", "status": "loaded"}
        if path == "/api/v1/models/unload":
            return 200, {"instance_id": "model-a"}
        if path == "/api/v1/models/download":
            return 200, {"job_id": "job_1", "status": "downloading"}
        if path == "/api/v1/models/download/status/job_1":
            return 200, {"job_id": "job_1", "status": "completed"}
        return 500, {}

    monkeypatch.setattr(client, "_request", fake_request)

    assert (await client.load_model("model-a", context_length=4096))["success"] is True
    assert (await client.unload_model("model-a"))["success"] is True
    assert (await client.download_model("model-a", "Q4_K_M"))["success"] is True
    assert (await client.download_status("job_1"))["status"] == "completed"

    assert calls[0] == ("POST", "/api/v1/models/load", {"model": "model-a", "context_length": 4096})
    assert calls[1] == ("POST", "/api/v1/models/unload", {"instance_id": "model-a"})


@pytest.mark.asyncio
async def test_lmstudio_client_generate_parses_native_chat(monkeypatch):
    client = LMStudioClient()

    async def fake_request(method, path, **kwargs):
        assert method == "POST"
        assert path == "/api/v1/chat"
        payload = kwargs["json"]
        assert payload["model"] == "model-a"
        assert payload["max_output_tokens"] == 25
        return 200, {
            "model_instance_id": "model-a",
            "output": [{"type": "message", "content": "answer"}],
            "stats": {"input_tokens": 3, "total_output_tokens": 1},
            "response_id": "resp_1",
        }

    monkeypatch.setattr(client, "_request", fake_request)
    result = await client.generate("hello", model="model-a", max_tokens=25)

    assert result["success"] is True
    assert result["content"] == "answer"
    assert result["usage"]["input_tokens"] == 3


@pytest.mark.asyncio
async def test_lmstudio_client_http_error_returns_failure(monkeypatch):
    client = LMStudioClient()

    async def fake_request(method, path, **kwargs):
        return 503, {"error": "down"}

    monkeypatch.setattr(client, "_request", fake_request)
    result = await client.generate("hello", model="model-a")

    assert result["success"] is False
    assert "HTTP 503" in result["error"]


@pytest.mark.asyncio
async def test_route_generate_dispatches_to_lmstudio(monkeypatch):
    async def fake_generate_lmstudio(prompt, model, temperature, max_tokens):
        return {
            "success": True,
            "content": f"{model}:{prompt}",
            "model": f"lmstudio::{model}",
            "usage": {},
        }

    monkeypatch.setattr(model_router, "_generate_lmstudio", fake_generate_lmstudio)
    result = await model_router.route_generate("hello", model="lmstudio::model-a", temperature=0.1, max_tokens=9)

    assert result["success"] is True
    assert result["content"] == "model-a:hello"


@pytest.mark.asyncio
async def test_lmstudio_generate_endpoint(monkeypatch):
    from src.api.endpoints import lmstudio as lmstudio_endpoint

    async def fake_generate(**kwargs):
        assert kwargs["model"] == "model-a"
        assert kwargs["prompt"] == "hello"
        return {"success": True, "content": "answer", "model": "model-a"}

    monkeypatch.setattr(lmstudio_endpoint.lmstudio_client, "generate", fake_generate)
    result = await lmstudio_endpoint.lmstudio_generate({"model": "model-a", "prompt": "hello"})

    assert result["success"] is True
    assert result["content"] == "answer"


@pytest.mark.asyncio
async def test_lmstudio_models_endpoint(monkeypatch):
    from src.api.endpoints import lmstudio as lmstudio_endpoint

    async def fake_list_models():
        return {"success": True, "models": [{"key": "model-a"}], "count": 1}

    monkeypatch.setattr(lmstudio_endpoint.lmstudio_client, "list_models", fake_list_models)
    result = await lmstudio_endpoint.lmstudio_list_models()

    assert result["success"] is True
    assert result["count"] == 1

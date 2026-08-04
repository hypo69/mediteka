# -*- coding: utf-8 -*-

from src.models import llama_registry


class DummyConfig:
    def __init__(self, section):
        self.section = section

    def get_section(self, name):
        assert name == "llama_cpp"
        return self.section


def test_configured_llama_servers_use_explicit_ports(monkeypatch):
    dummy = DummyConfig(
        {
            "host": "127.0.0.1",
            "port": 9780,
            "models": [
                {"alias": "coder", "model_path": "D:/models/coder.gguf", "port": 9791},
                {"alias": "chat", "model_path": "D:/models/chat.gguf", "port": 9792},
            ],
        }
    )
    monkeypatch.setattr("src.core.config.config", dummy)

    servers = llama_registry.get_configured_llama_servers()

    assert [(s.alias, s.port) for s in servers] == [("coder", 9791), ("chat", 9792)]


def test_resolve_llama_server_matches_alias_path_and_filename(monkeypatch):
    dummy = DummyConfig(
        {
            "host": "127.0.0.1",
            "port": 9780,
            "models": [
                {"alias": "coder", "model_path": "D:/models/qwen-coder.gguf", "port": 9791},
            ],
        }
    )
    monkeypatch.setattr("src.core.config.config", dummy)

    assert llama_registry.resolve_llama_server("coder").port == 9791
    assert llama_registry.resolve_llama_server("D:/models/qwen-coder.gguf").port == 9791
    assert llama_registry.resolve_llama_server("qwen-coder.gguf").port == 9791

# -*- coding: utf-8 -*-

import json
import logging
from datetime import date, timedelta

import pytest

from src.logger import DailyLineRotatingFileHandler, get_log_settings
from src.api.endpoints import logs as logs_api


def _formatter() -> logging.Formatter:
    return logging.Formatter("%(levelname)s | %(name)s | %(message)s")


def test_daily_line_handler_writes_warning_and_error_only(tmp_path):
    handler = DailyLineRotatingFileHandler(tmp_path, max_lines=10, retention_days=7)
    handler.setLevel(logging.WARNING)
    handler.setFormatter(_formatter())

    logger = logging.getLogger("tests.logging.warning_only")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    logger.info("success should not be written")
    logger.warning("warning should be written")
    logger.error("error should be written")
    handler.close()

    files = list(tmp_path.glob("aiassistant-*.log"))
    assert len(files) == 1
    content = files[0].read_text(encoding="utf-8")
    assert "success should not be written" not in content
    assert "warning should be written" in content
    assert "error should be written" in content


def test_daily_line_handler_rotates_by_line_count(tmp_path):
    handler = DailyLineRotatingFileHandler(tmp_path, max_lines=2, retention_days=7)
    handler.setLevel(logging.WARNING)
    handler.setFormatter(_formatter())

    logger = logging.getLogger("tests.logging.rotation")
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    logger.warning("line 1")
    logger.warning("line 2")
    logger.warning("line 3")
    handler.close()

    files = sorted(tmp_path.glob("aiassistant-*.log"))
    assert [f.name for f in files] == [
        f"aiassistant-{date.today().isoformat()}-001.log",
        f"aiassistant-{date.today().isoformat()}-002.log",
    ]
    assert "line 3" in files[1].read_text(encoding="utf-8")


def test_daily_line_handler_removes_expired_daily_files(tmp_path):
    old_day = (date.today() - timedelta(days=3)).isoformat()
    old_file = tmp_path / f"aiassistant-{old_day}-001.log"
    old_file.write_text("old warning\n", encoding="utf-8")

    handler = DailyLineRotatingFileHandler(tmp_path, max_lines=10, retention_days=2)
    handler.close()

    assert not old_file.exists()


def test_get_log_settings_reads_config_from_current_directory(tmp_path, monkeypatch):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "logging": {
                    "level": "ERROR",
                    "log_dir": str(tmp_path / "logs"),
                    "max_lines_per_file": 1234,
                    "retention_days": 9,
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    settings = get_log_settings()

    assert settings["level"] == "ERROR"
    assert settings["log_dir"] == str(tmp_path / "logs")
    assert settings["max_lines_per_file"] == 1234
    assert settings["retention_days"] == 9


@pytest.mark.asyncio
async def test_logs_api_lists_and_reads_latest_file(tmp_path, monkeypatch):
    log_file = tmp_path / f"aiassistant-{date.today().isoformat()}-001.log"
    log_file.write_text(
        "\n".join(
            [
                "2026-05-07 10:00:00 | WARNING | app | fn | 1 | first warning",
                "2026-05-07 10:01:00 | ERROR | app | fn | 2 | second error",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        logs_api,
        "get_log_settings",
        lambda: {
            "log_dir": str(tmp_path),
            "level": "WARNING",
            "max_lines_per_file": 5000,
            "retention_days": 7,
        },
    )

    files = await logs_api.list_log_files()
    assert files["success"] is True
    assert files["files"][0]["name"] == log_file.name

    page = await logs_api.get_logs(file="", lines=10, level="ERROR", search="", offset=0)
    assert page["success"] is True
    assert page["file"] == log_file.name
    assert page["returned"] == 1
    assert "second error" in page["lines"][0]


@pytest.mark.asyncio
async def test_logs_api_lists_install_log_for_logs_tab(tmp_path, monkeypatch):
    install_log = tmp_path / "aiassistant-install.log"
    install_log.write_text(
        "2026-05-07 10:00:00 | ERROR   | install | LM Studio installer error\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        logs_api,
        "get_log_settings",
        lambda: {
            "log_dir": str(tmp_path),
            "level": "WARNING",
            "max_lines_per_file": 5000,
            "retention_days": 7,
        },
    )

    files = await logs_api.list_log_files()
    names = [f["name"] for f in files["files"]]
    assert "aiassistant-install.log" in names

    page = await logs_api.get_logs(file="aiassistant-install.log", lines=10, level="ERROR", search="LM Studio", offset=0)
    assert page["success"] is True
    assert page["returned"] == 1
    assert "LM Studio installer error" in page["lines"][0]


@pytest.mark.asyncio
async def test_logs_health_counts_warnings_and_errors(tmp_path, monkeypatch):
    (tmp_path / f"aiassistant-{date.today().isoformat()}-001.log").write_text(
        "\n".join(
            [
                "2026-05-07 10:00:00 | WARNING | app | fn | 1 | warn",
                "2026-05-07 10:01:00 | ERROR | app | fn | 2 | err",
                "2026-05-07 10:02:00 | WARNING | app | fn | 3 | HTTP GET /missing -> 404 (0.125s)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        logs_api,
        "get_log_settings",
        lambda: {
            "log_dir": str(tmp_path),
            "level": "WARNING",
            "max_lines_per_file": 5000,
            "retention_days": 7,
        },
    )

    health = await logs_api.get_logs_health()

    assert health["success"] is True
    assert health["status"] == "critical"
    assert health["metrics"]["warnings_count"] == 2
    assert health["metrics"]["errors_count"] == 1
    assert health["metrics"]["api_requests"] == 1
    assert health["metrics"]["avg_response_time"] == 0.125

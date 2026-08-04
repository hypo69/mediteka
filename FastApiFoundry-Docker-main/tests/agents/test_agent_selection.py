# -*- coding: utf-8 -*-

from src.api.endpoints.agent import select_agent_name


class TestAgentSelection:
    def test_auto_selects_computer_admin_when_available(self):
        registry = {"powershell": object(), "computer_admin": object()}

        selected = select_agent_name("проверь систему", "auto", registry)

        assert selected == "computer_admin"

    def test_explicit_agent_is_preserved(self):
        registry = {"powershell": object(), "computer_admin": object()}

        selected = select_agent_name("покажи файлы", "powershell", registry)

        assert selected == "powershell"

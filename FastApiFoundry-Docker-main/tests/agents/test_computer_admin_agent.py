# -*- coding: utf-8 -*-

from src.agents.base import ToolDefinition
from src.agents.computer_admin_agent import ComputerAdminAgent


class TestComputerAdminAgent:
    def test_agent_exposes_admin_tools(self):
        agent = ComputerAdminAgent(foundry_client=object())

        tool_names = {tool.name for tool in agent.tools}

        assert "invoke_os_diagnostic" in tool_names
        assert "run_powershell_check" in tool_names
        assert "run_python_check" in tool_names
        assert "get_system_info" in tool_names
        assert "get_event_logs" in tool_names
        assert "get_defender_status" in tool_names
        assert "cleanup_temp_files" in tool_names
        assert "control_service" in tool_names

    def test_tools_openai_returns_function_schema(self):
        class DemoAgent(ComputerAdminAgent):
            @property
            def tools(self):
                return [
                    ToolDefinition(
                        name="demo_tool",
                        description="Demo tool",
                        parameters={"type": "object", "properties": {}},
                    )
                ]

        tools = DemoAgent(foundry_client=object()).tools_openai()

        assert tools == [
            {
                "type": "function",
                "function": {
                    "name": "demo_tool",
                    "description": "Demo tool",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: PowerShell MCP Integration Tests
# =============================================================================
# Description:
#   Integration testing of PowerShell command execution via subprocess.
#
# File: tests/integration/test_powershell_mcp.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Moved to tests/integration/ (was in scripts/)
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import subprocess
import json
import pytest


class TestPowerShellMCP:
    """Integration tests for PowerShell MCP server execution."""

    def test_execution_simple(self):
        """Validation of basic PowerShell version command."""
        args = ["powershell", "-Command", "$PSVersionTable.PSVersion.Major"]
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8")

        assert result.returncode == 0
        assert int(result.stdout.strip()) >= 5

    def test_json_rpc_simulation(self):
        """Simulation of JSON data passing through PowerShell stdin."""
        payload = json.dumps({"params": {"message": "Ai Assistant_QA"}})
        script = "$input | ConvertFrom-Json | ForEach-Object { $_.params.message }"

        proc = subprocess.Popen(
            ["powershell", "-Command", script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        stdout, _ = proc.communicate(input=payload)

        assert "Ai Assistant_QA" in stdout

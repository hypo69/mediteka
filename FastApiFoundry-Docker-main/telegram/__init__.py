# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Telegram Bots Launcher
# =============================================================================
# Description:
#   Runs admin_bot and helpdesk_bot concurrently as asyncio tasks.
#   Called from run.py on startup when tokens are configured.
#
#   Usage (standalone):
#       python -m telegram
#
# File: telegram/__init__.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import logging

logger = logging.getLogger(__name__)


async def start_all_bots() -> None:
    """Start admin_bot and helpdesk_bot concurrently.

    Each bot exits silently if its token is not configured.
    """
    from .admin_bot    import admin_bot
    from .helpdesk_bot import helpdesk_bot

    await asyncio.gather(
        admin_bot.start(),
        helpdesk_bot.start(),
        return_exceptions=True,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_all_bots())

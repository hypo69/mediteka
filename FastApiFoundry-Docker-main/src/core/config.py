# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Единая конфигурация проекта
# =============================================================================
# Описание:
#   Реэкспорт singleton-экземпляра Config из config_manager.
#   Используется всеми модулями src/ через: from src.core.config import config
#
# File: config.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Changes in 0.6.1:
#   - Removed deprecated `settings` alias (use `config` directly)
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from config_manager import config

__all__ = ["config"]

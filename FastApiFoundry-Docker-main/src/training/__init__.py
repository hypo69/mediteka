# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Training Module — Fine-tuning & Dataset Management
# =============================================================================
# Description:
#   Entry point for the training subsystem.
#   Exposes dataset storage, QA pair collection, and fine-tuning pipeline.
#
# File: __init__.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# Changes in 0.7.1:
#   - Initial training module scaffold
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from .dataset_store import DatasetStore, QAPair, QAPairStatus
from .trainer import FineTuner

__all__ = ["DatasetStore", "QAPair", "QAPairStatus", "FineTuner"]

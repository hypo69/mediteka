# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: API Endpoints Package
# =============================================================================
# Description:
#   Aggregates and exports routers from all endpoint modules.
#
# File: __init__.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from fastapi import APIRouter
from .rag import router as rag_router

# Aggregate router re-exported as `router` for backward compatibility with main.py
router = APIRouter()
router.include_router(rag_router)

__all__ = ['router']
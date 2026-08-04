#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Simple Data Models for FastAPI Foundry
# =============================================================================
# Description:
#   Simple functions for creating standard API responses
#   No Pydantic - only dictionaries
#
# File: models.py
# Project: Ai Assistant (Docker)
# Version: 0.2.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: December 9, 2025
# =============================================================================

from datetime import datetime

def create_generate_response(success: bool, content: str = None, model: str = None, error: str = None) -> dict:
    """Create a text generation response.

    Args:
        success: Whether generation succeeded.
        content: Generated text content.
        model:   Model ID used for generation.
        error:   Error message if success is False.

    Returns:
        dict: success, content, model, error.
    """
    return {
        "success": success,
        "content": content,
        "model": model,
        "error": error
    }

def create_health_response(status: str, foundry_status: str, rag_available: bool) -> dict:
    """Create a health check response.

    Args:
        status:         Overall API status string.
        foundry_status: Foundry service status string.
        rag_available:  Whether the RAG system is available.

    Returns:
        dict: status, foundry_status, rag_available, timestamp (ISO 8601).
    """
    return {
        "status": status,
        "foundry_status": foundry_status,
        "rag_available": rag_available,
        "timestamp": datetime.now().isoformat()
    }

def create_error_response(error: str, detail: str = None) -> dict:
    """Create an error response.

    Args:
        error:  Short error description.
        detail: Optional extended detail message.

    Returns:
        dict: error, detail.
    """
    return {
        "error": error,
        "detail": detail
    }

def create_models_response(success: bool, models: list = None, error: str = None) -> dict:
    """Create a models list response.

    Args:
        success: Whether the request succeeded.
        models:  List of model dicts.
        error:   Error message if success is False.

    Returns:
        dict: success, models (list, empty if None), error.
    """
    return {
        "success": success,
        "models": models or [],
        "error": error
    }
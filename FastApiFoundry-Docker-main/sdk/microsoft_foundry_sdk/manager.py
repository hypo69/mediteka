# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Foundry Local Manager — Model Lifecycle
# =============================================================================
# Description:
#   Wrapper around FoundryLocalManager from foundry-local-sdk.
#   Handles initialization, model catalog, load/unload, and status checks.
#
# File: manager.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Guard: foundry-local-sdk is optional
FOUNDRY_SDK_AVAILABLE = False
try:
    from foundry_local_sdk import Configuration, FoundryLocalManager as _Manager
    FOUNDRY_SDK_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ foundry-local-sdk not installed. Run: pip install foundry-local-sdk")


class FoundryManager:
    """Manages Microsoft Foundry Local model lifecycle.

    Wraps FoundryLocalManager singleton. Provides model catalog access,
    load/unload, and status inspection.

    Example:
        >>> mgr = FoundryManager(app_name="my_app")
        >>> mgr.initialize()
        >>> models = mgr.list_models()
        >>> mgr.load_model("phi-4")
        >>> mgr.unload_model("phi-4")
    """

    def __init__(self, app_name: str = "fastapi_foundry") -> None:
        self.app_name = app_name
        self._manager = None

    def initialize(self) -> bool:
        """Initialize Foundry Local manager.

        Returns:
            bool: True if initialized successfully.
        """
        if not FOUNDRY_SDK_AVAILABLE:
            logger.error("❌ foundry-local-sdk not available")
            return False
        try:
            _Manager.initialize(Configuration(app_name=self.app_name))
            self._manager = _Manager.instance
            logger.info(f"✅ Foundry Local initialized: app={self.app_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Foundry init failed: {e}")
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        """List all models available in the local catalog.

        Returns:
            List of model info dicts with keys: alias, id, size, quantization.
        """
        if not self._manager:
            return []
        try:
            return [
                {
                    "alias": m.alias,
                    "id": m.model_id,
                    "size": getattr(m, "size", None),
                    "quantization": getattr(m, "quantization", None),
                }
                for m in self._manager.catalog.list_models()
            ]
        except Exception as e:
            logger.error(f"❌ list_models failed: {e}")
            return []

    def load_model(self, model_alias: str) -> bool:
        """Download (if needed) and load a model into memory.

        Args:
            model_alias: Model alias, e.g. 'phi-4' or 'qwen2.5-0.5b'.

        Returns:
            bool: True if loaded successfully.
        """
        if not self._manager:
            return False
        try:
            model = self._manager.catalog.get_model(model_alias)
            model.load()
            logger.info(f"✅ Model loaded: {model_alias}")
            return True
        except Exception as e:
            logger.error(f"❌ load_model '{model_alias}' failed: {e}")
            return False

    def unload_model(self, model_alias: str) -> bool:
        """Unload a model from memory.

        Args:
            model_alias: Model alias to unload.

        Returns:
            bool: True if unloaded successfully.
        """
        if not self._manager:
            return False
        try:
            model = self._manager.catalog.get_model(model_alias)
            model.unload()
            logger.info(f"✅ Model unloaded: {model_alias}")
            return True
        except Exception as e:
            logger.error(f"❌ unload_model '{model_alias}' failed: {e}")
            return False

    def get_model_status(self, model_alias: str) -> Dict[str, Any]:
        """Get current status of a model.

        Args:
            model_alias: Model alias.

        Returns:
            dict with keys: alias, loaded, endpoint_url.
        """
        if not self._manager:
            return {"alias": model_alias, "loaded": False, "endpoint_url": None}
        try:
            model = self._manager.catalog.get_model(model_alias)
            return {
                "alias": model_alias,
                "loaded": getattr(model, "is_loaded", False),
                "endpoint_url": getattr(model, "endpoint_url", None),
            }
        except Exception as e:
            return {"alias": model_alias, "loaded": False, "error": str(e)}

    def get_chat_client(self, model_alias: str) -> Optional[Any]:
        """Get OpenAI-compatible chat client for a loaded model.

        Args:
            model_alias: Model alias (must be loaded first).

        Returns:
            OpenAI-compatible client or None on failure.
        """
        if not self._manager:
            return None
        try:
            model = self._manager.catalog.get_model(model_alias)
            return model.get_chat_client()
        except Exception as e:
            logger.error(f"❌ get_chat_client '{model_alias}' failed: {e}")
            return None

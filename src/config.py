# -*- coding: utf-8 -*-
import os
from pathlib import Path
from src.utils.jjson import j_loads_ns
from header import __root__

CONFIG_FILE = __root__ / "config.json"

# Load global configuration
global_settings = j_loads_ns(CONFIG_FILE)

# Expose main sections for easier import
server_cfg = getattr(global_settings, "server", None)
ai_cfg = getattr(global_settings, "ai", None)
tts_cfg = getattr(global_settings, "tts", None)
logging_cfg = getattr(global_settings, "logging", None)

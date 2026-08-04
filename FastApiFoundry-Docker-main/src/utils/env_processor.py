# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Environment Variables Processor for Config
# =============================================================================
# Description:
#   Utility for substituting environment variables in config.json.
#   Supports ${VAR_NAME:default_value} syntax.
#
# Examples:
#   from src.utils.env_processor import process_config
#   config = process_config('config.json')
#
# File: src/utils/env_processor.py
# Project: Ai Assistant (Docker)
# Version: 0.5.5
# Changes in 0.5.5:
#   - Added try/except with logging in process_config, substitute_env_vars,
#     save_processed_config
#   - load_env_variables now logs on failure instead of silently returning False
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Union

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_env_variables() -> bool:
    """Load environment variables from .env file.

    Returns:
        bool: True if .env was found and loaded.
    """
    env_path = Path('.env')
    if not env_path.exists():
        return False
    try:
        load_dotenv(env_path)
        return True
    except Exception as e:
        # .env exists but dotenv failed to parse it (encoding, permissions, etc.)
        logger.error(f'❌ Failed to load .env: {e}')
        return False


def substitute_env_vars(value: str) -> Union[str, int, float, bool, list]:
    """Substitute environment variables in a string.

    Supported formats:
        ${VAR_NAME}          — required variable
        ${VAR_NAME:default}  — with default value

    Args:
        value: String potentially containing ${...} placeholders.

    Returns:
        Substituted and type-converted value (str, int, float, bool, or list).

    Raises:
        ValueError: If a required variable is not set.
    """
    if not isinstance(value, str):
        return value

    pattern = r'\$\{([^}:]+)(?::([^}]*))?}'

    def _replace(match: re.Match) -> str:
        var_name = match.group(1)
        default = match.group(2)
        env_val = os.getenv(var_name)
        if env_val is not None:
            return env_val
        if default is not None:
            return default
        # Required variable missing — caller must handle
        raise ValueError(f"Required environment variable '{var_name}' is not set")

    try:
        result = re.sub(pattern, _replace, value)
    except ValueError:
        raise
    except Exception as e:
        # Regex substitution failed for unexpected reason
        logger.error(f'❌ substitute_env_vars failed for value={value!r}: {e}')
        return value

    return convert_type(result)


def convert_type(value: str) -> Union[str, int, float, bool, list]:
    """Convert a string to the most appropriate Python type.

    Args:
        value: String to convert.

    Returns:
        Converted value: bool for 'true'/'false', int/float for numbers,
        list for comma-separated, str otherwise.
    """
    if not isinstance(value, str):
        return value
    if value.lower() in ('true', 'yes', '1', 'on'):
        return True
    if value.lower() in ('false', 'no', '0', 'off'):
        return False
    try:
        return float(value) if '.' in value else int(value)
    except ValueError:
        pass
    if ',' in value:
        return [item.strip() for item in value.split(',')]
    return value


def process_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively substitute env vars in a config dict.

    Args:
        data: Configuration dict to process.

    Returns:
        dict: Processed configuration with all ${...} placeholders substituted.
    """
    result: Dict[str, Any] = {}
    for key, val in data.items():
        if isinstance(val, dict):
            result[key] = process_dict(val)
        elif isinstance(val, list):
            result[key] = [
                process_dict(item) if isinstance(item, dict)
                else substitute_env_vars(item) if isinstance(item, str)
                else item
                for item in val
            ]
        elif isinstance(val, str):
            result[key] = substitute_env_vars(val)
        else:
            result[key] = val
    return result


def process_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load and process a config file, substituting env vars.

    Args:
        config_path: Path to config.json.

    Returns:
        Processed configuration dict.

    Raises:
        FileNotFoundError: Config file not found.
        json.JSONDecodeError: Invalid JSON in config file.
        ValueError: Required env variable not set.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f'Config file not found: {config_path}')

    load_env_variables()

    try:
        with open(config_path, encoding='utf-8') as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        # Config file is not valid JSON — cannot proceed
        logger.error(f'❌ Invalid JSON in {config_path}: {e}')
        raise
    except OSError as e:
        logger.error(f'❌ Cannot read {config_path}: {e}')
        raise

    try:
        return process_dict(raw)
    except ValueError as e:
        # Missing required env variable — propagate with context
        logger.error(f'❌ Env substitution failed in {config_path}: {e}')
        raise


def validate_config(cfg: Dict[str, Any]) -> bool:
    """Validate processed configuration.

    Args:
        cfg: Configuration dict to check.

    Returns:
        bool: True if all required sections (fastapi_server, foundry_ai, security) are present.
    """
    required = ['fastapi_server', 'foundry_ai', 'security']
    for section in required:
        if section not in cfg:
            logger.error(f'❌ Missing required config section: {section}')
            return False
    if not cfg.get('security', {}).get('api_key'):
        logger.warning('⚠️ API_KEY not set in security section')
    if not cfg.get('security', {}).get('secret_key'):
        logger.warning('⚠️ SECRET_KEY not set in security section')
    return True


def save_processed_config(cfg: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """Save processed configuration to a file.

    Args:
        cfg: Configuration dict.
        output_path: Destination file path.
    """
    output_path = Path(output_path)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except OSError as e:
        # Disk write failed — caller decides whether to abort
        logger.error(f'❌ Cannot write processed config to {output_path}: {e}')
        raise


if __name__ == '__main__':
    import sys

    _cfg_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    try:
        print(f'🔧 Processing config: {_cfg_file}')
        _cfg = process_config(_cfg_file)
        print('✅ Config processed successfully!')
        if validate_config(_cfg):
            print('✅ Config validation passed!')
        else:
            print('⚠️ Config validation warnings found')
        _debug = Path(_cfg_file).with_suffix('.processed.json')
        save_processed_config(_cfg, _debug)
        print(f'💾 Saved to: {_debug}')
    except Exception as exc:
        print(f'❌ Error: {exc}')
        sys.exit(1)

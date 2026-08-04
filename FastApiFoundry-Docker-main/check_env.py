# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Environment Variables Checker
# =============================================================================
# Description:
#   Utility for checking and validating environment variables
#   Checks for the presence of required variables and their correctness
#
# Examples:
#   python311 check_env.py
#   python311 check_env.py --show-secrets
#
# File: check_env.py
# Project: Ai Assistant (Docker)
# Version: 0.6.0
# Changes in 0.6.0:
#   - MIT License update
#   - Unified headers and return type hints
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# =============================================================================

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import re

def load_env_file() -> bool:
    """Loading variables from .env file"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found!")
        print("💡 Copy .env.example to .env and fill with your data")
        return False
    
    load_dotenv()
    print(f"✅ Loaded .env from {env_path.absolute()}")
    return True

def check_github_config(show_secrets: bool = False) -> None:
    """Checking GitHub configuration"""
    print("\n🐙 GitHub Configuration:")
    
    user = os.getenv('GITHUB_USER')
    password = os.getenv('GITHUB_PASSWORD') 
    pat = os.getenv('GITHUB_PAT')
    
    if user:
        print(f"  ✅ GITHUB_USER: {user}")
    else:
        print("  ⚠️  GITHUB_USER: not set")
    
    if password:
        value = password if show_secrets else "***"
        print(f"  ✅ GITHUB_PASSWORD: {value}")
    else:
        print("  ⚠️  GITHUB_PASSWORD: not set")
    
    if pat:
        if show_secrets:
            print(f"  ✅ GITHUB_PAT: {pat}")
        else:
            # Show only the first and last characters
            masked = pat[:8] + "..." + pat[-4:] if len(pat) > 12 else "***"
            print(f"  ✅ GITHUB_PAT: {masked}")
        
        # Checking PAT format
        if pat.startswith('ghp_'):
            print("  ✅ PAT format: valid (classic)")
        elif pat.startswith('github_pat_'):
            print("  ✅ PAT format: valid (fine-grained)")
        else:
            print("  ⚠️  PAT format: unknown (should start with 'ghp_' or 'github_pat_')")
    else:
        print("  ❌ GITHUB_PAT: not set (required for API access)")

def check_api_config(show_secrets: bool = False) -> None:
    """Checking API configuration"""
    print("\n🔑 API Configuration:")
    
    api_key = os.getenv('API_KEY')
    secret_key = os.getenv('SECRET_KEY')
    cors_origins = os.getenv('CORS_ORIGINS')
    
    if api_key:
        value = api_key if show_secrets else "***"
        print(f"  ✅ API_KEY: {value}")
        
        if len(api_key) < 16:
            print("  ⚠️  API_KEY too short (recommended: 32+ chars)")
    else:
        print("  ❌ API_KEY: not set")
    
    if secret_key:
        value = secret_key if show_secrets else "***"
        print(f"  ✅ SECRET_KEY: {value}")
        
        if len(secret_key) < 32:
            print("  ⚠️  SECRET_KEY too short (recommended: 64+ chars)")
    else:
        print("  ❌ SECRET_KEY: not set")
    
    if cors_origins:
        print(f"  ✅ CORS_ORIGINS: {cors_origins}")
    else:
        print("  ⚠️  CORS_ORIGINS: not set (using defaults)")

def check_foundry_config() -> None:
    """Checking Foundry configuration"""
    print("\n🤖 Foundry AI Configuration:")
    
    base_url = os.getenv('FOUNDRY_BASE_URL', 'http://localhost:63995/v1')
    api_key = os.getenv('FOUNDRY_API_KEY')
    timeout = os.getenv('FOUNDRY_TIMEOUT', '30')
    
    print(f"  ✅ FOUNDRY_BASE_URL: {base_url}")
    
    # Checking URL format
    if not re.match(r'https?://.*', base_url):
        print("  ⚠️  Invalid URL format")
    
    if api_key:
        print("  ✅ FOUNDRY_API_KEY: ***")
    else:
        print("  ⚠️  FOUNDRY_API_KEY: not set (optional)")
    
    try:
        timeout_int = int(timeout)
        print(f"  ✅ FOUNDRY_TIMEOUT: {timeout_int}s")
        if timeout_int < 10:
            print("  ⚠️  Timeout too low (recommended: 30+)")
    except ValueError:
        print(f"  ❌ FOUNDRY_TIMEOUT: invalid value '{timeout}'")

def check_database_config() -> None:
    """Checking Database configuration"""
    print("\n💾 Database Configuration:")
    
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        # Masking password in URL
        masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:***@', db_url)
        print(f"  ✅ DATABASE_URL: {masked_url}")
        
        if db_url.startswith('sqlite:'):
            print("  ✅ Database type: SQLite")
        elif db_url.startswith('postgresql:'):
            print("  ✅ Database type: PostgreSQL")
        elif db_url.startswith('mysql:'):
            print("  ✅ Database type: MySQL")
        else:
            print("  ⚠️  Unknown database type")
    else:
        print("  ⚠️  DATABASE_URL: not set (using defaults)")

def check_external_apis(show_secrets: bool = False) -> None:
    """Checking external APIs"""
    print("\n🌍 External APIs:")
    
    apis = {
        'OPENAI_API_KEY': 'sk-',
        'ANTHROPIC_API_KEY': 'sk-ant-',
        'HUGGINGFACE_API_KEY': 'hf_'
    }
    
    for key, prefix in apis.items():
        value = os.getenv(key)
        if value:
            display_value = value if show_secrets else "***"
            print(f"  ✅ {key}: {display_value}")
            
            if not value.startswith(prefix):
                print(f"  ⚠️  {key}: unexpected format (should start with '{prefix}')")
        else:
            print(f"  ⚠️  {key}: not set")

def check_environment() -> None:
    """Checking environment mode"""
    print("\n🌍 Environment Mode:")
    
    env = os.getenv('ENVIRONMENT', 'development')
    debug = os.getenv('DEBUG', 'true').lower()
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    
    print(f"  ✅ ENVIRONMENT: {env}")
    print(f"  ✅ DEBUG: {debug}")
    print(f"  ✅ LOG_LEVEL: {log_level}")
    
    if env == 'production' and debug == 'true':
        print("  ⚠️  WARNING: DEBUG=true in production!")
    
    if env == 'development' and log_level == 'ERROR':
        print("  ⚠️  LOG_LEVEL=ERROR in development (consider INFO or DEBUG)")

def generate_secure_keys() -> None:
    """Generating secure keys"""
    print("\n🔐 Generate Secure Keys:")
    print("Run these commands to generate secure keys:")
    print()
    print("python311 -c \"import secrets; print(f'API_KEY={secrets.token_urlsafe(32)}')\"")
    print("python311 -c \"import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(64)}')\"")

def main() -> None:
    parser = argparse.ArgumentParser(description='Check environment variables')
    parser.add_argument('--show-secrets', action='store_true', 
                       help='Show actual secret values (use with caution)')
    parser.add_argument('--generate-keys', action='store_true',
                       help='Show commands to generate secure keys')
    
    args = parser.parse_args()
    
    print("🔍 FastAPI Foundry - Environment Variables Checker")
    print("=" * 60)
    
    if not load_env_file():
        sys.exit(1)
    
    # Checking all sections
    check_github_config(args.show_secrets)
    check_api_config(args.show_secrets)
    check_foundry_config()
    check_database_config()
    check_external_apis(args.show_secrets)
    check_environment()
    
    if args.generate_keys:
        generate_secure_keys()
    
    print("\n" + "=" * 60)
    print("✅ Environment check completed!")
    
    if not args.show_secrets:
        print("💡 Use --show-secrets to see actual values")

if __name__ == "__main__":
    main()
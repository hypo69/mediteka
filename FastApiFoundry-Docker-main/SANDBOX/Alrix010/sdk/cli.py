#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI Foundry SDK CLI
# =============================================================================
# Описание:
#   Командная строка для работы с FastAPI Foundry через SDK
#
# File: cli.py
# Project: Ai Assistant (Docker)
# Version: 0.4.0
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

import argparse
import json
from .client import FoundryClient
from .exceptions import FoundryError

def cmd_health(client):
    """Проверка здоровья системы"""
    health = client.health()
    print(json.dumps({
        "status": health.status,
        "foundry_status": health.foundry_status,
        "rag_chunks": health.rag_chunks,
        "models_count": health.models_count
    }, indent=2))

def cmd_models(client):
    """Список моделей"""
    models = client.list_models()
    for model in models:
        print(f"{model.id} ({model.provider}) - {model.status}")

def cmd_generate(client, prompt, model=None, max_tokens=None, use_rag=True):
    """Генерация текста"""
    response = client.generate(
        prompt=prompt,
        model=model,
        max_tokens=max_tokens,
        use_rag=use_rag
    )
    
    if response.success:
        print(response.content)
    else:
        print(f"Error: {response.error}")

def cmd_rag_search(client, query, top_k=5):
    """RAG поиск"""
    results = client.rag_search(query, top_k)
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.get('source', 'Unknown')} (score: {result.get('score', 0):.3f})")
        print(f"   {result.get('text', '')[:100]}...")

def main():
    parser = argparse.ArgumentParser(description="FastAPI Foundry SDK CLI")
    parser.add_argument("--url", default="http://localhost:9696", help="API URL")
    parser.add_argument("--api-key", help="API Key")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Health command
    subparsers.add_parser("health", help="Check system health")
    
    # Models command
    subparsers.add_parser("models", help="List available models")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate text")
    gen_parser.add_argument("prompt", help="Text prompt")
    gen_parser.add_argument("--model", help="Model ID")
    gen_parser.add_argument("--max-tokens", type=int, help="Max tokens")
    gen_parser.add_argument("--no-rag", action="store_true", help="Disable RAG")
    
    # RAG search command
    rag_parser = subparsers.add_parser("rag", help="RAG search")
    rag_parser.add_argument("query", help="Search query")
    rag_parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        with FoundryClient(base_url=args.url, api_key=args.api_key) as client:
            if args.command == "health":
                cmd_health(client)
            elif args.command == "models":
                cmd_models(client)
            elif args.command == "generate":
                cmd_generate(client, args.prompt, args.model, args.max_tokens, not args.no_rag)
            elif args.command == "rag":
                cmd_rag_search(client, args.query, args.top_k)
                
    except FoundryError as e:
        print(f"SDK Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
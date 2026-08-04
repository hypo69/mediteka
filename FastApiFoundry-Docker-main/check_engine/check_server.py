#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тест сервера FastAPI Foundry
# =============================================================================
# Описание:
#   Быстрый тест доступности сервера и основных endpoints
#
# File: test_server.py
# Project: Ai Assistant (Docker)
# Version: 0.2.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

import requests
import sys
import time

def test_endpoint(url, name):
    """Тест endpoint"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: OK ({response.status_code})")
            return True
        else:
            print(f"❌ {name}: ERROR ({response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: CONNECTION ERROR - {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование FastAPI Foundry сервера...")
    print("=" * 50)
    
    base_url = "http://localhost:9696"
    
    # Список endpoints для тестирования
    endpoints = [
        (f"{base_url}/", "Главная страница"),
        (f"{base_url}/api", "API Info"),
        (f"{base_url}/api/v1/health", "Health Check"),
        (f"{base_url}/api/v1/models", "Models List"),
        (f"{base_url}/docs", "API Documentation"),
    ]
    
    results = []
    for url, name in endpoints:
        result = test_endpoint(url, name)
        results.append(result)
        time.sleep(0.5)  # Небольшая пауза между запросами
    
    print("=" * 50)
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"🎉 Все тесты пройдены! ({success_count}/{total_count})")
        print(f"🌐 Сервер доступен: {base_url}")
        print(f"📚 Документация: {base_url}/docs")
        return 0
    else:
        print(f"⚠️  Некоторые тесты не прошли: {success_count}/{total_count}")
        print("🔧 Проверьте, что сервер запущен на порту 8000")
        return 1

if __name__ == "__main__":
    sys.exit(main())
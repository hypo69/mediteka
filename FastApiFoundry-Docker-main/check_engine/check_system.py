# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Комплексное тестирование FastAPI Foundry
# =============================================================================
# Описание:
#   Автоматическое тестирование всех компонентов системы:
#   - Health check API
#   - Foundry connection
#   - Models endpoint
#   - RAG system
#   - Chat functionality
#
# File: test_system.py
# Project: FastAPI Foundry
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import aiohttp
import json
from datetime import datetime

class SystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8002"
        self.foundry_url = "http://localhost:50477"
        self.results = []

    async def test_health(self):
        """Тест health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_result("✅ Health Check", "OK", data)
                        return True
                    else:
                        self.log_result("❌ Health Check", f"Status: {response.status}")
                        return False
        except Exception as e:
            self.log_result("❌ Health Check", f"Error: {str(e)}")
            return False

    async def test_foundry_connection(self):
        """Тест подключения к Foundry"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.foundry_url}/v1/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('data', [])
                        self.log_result("✅ Foundry Connection", f"OK, {len(models)} models", models[:2])
                        return True
                    else:
                        self.log_result("❌ Foundry Connection", f"Status: {response.status}")
                        return False
        except Exception as e:
            self.log_result("❌ Foundry Connection", f"Error: {str(e)}")
            return False

    async def test_models_endpoint(self):
        """Тест /models endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get('models', [])
                        self.log_result("✅ Models Endpoint", f"OK, {len(models)} models", [m.get('id', 'unknown') for m in models])
                        return True
                    else:
                        self.log_result("❌ Models Endpoint", f"Status: {response.status}")
                        return False
        except Exception as e:
            self.log_result("❌ Models Endpoint", f"Error: {str(e)}")
            return False

    async def test_rag_search(self):
        """Тест RAG поиска"""
        try:
            payload = {
                "query": "FastAPI configuration",
                "top_k": 3
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/v1/rag/search", json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        self.log_result("✅ RAG Search", f"OK, {len(results)} results", [r.get('content', '')[:50] + '...' for r in results])
                        return True
                    else:
                        self.log_result("❌ RAG Search", f"Status: {response.status}")
                        return False
        except Exception as e:
            self.log_result("❌ RAG Search", f"Error: {str(e)}")
            return False

    async def test_chat(self):
        """Тест чата с моделью"""
        try:
            payload = {
                "message": "Привет! Как дела?",
                "model": "deepseek-r1-distill-qwen-7b-generic-cpu:3",
                "use_rag": False
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/v1/chat", json=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get('response', '')
                        self.log_result("✅ Chat Test", f"OK, {len(response_text)} chars", response_text[:100] + '...')
                        return True
                    else:
                        self.log_result("❌ Chat Test", f"Status: {response.status}")
                        return False
        except Exception as e:
            self.log_result("❌ Chat Test", f"Error: {str(e)}")
            return False

    async def test_chat_with_rag(self):
        """Тест чата с RAG"""
        try:
            payload = {
                "message": "Как настроить FastAPI Foundry?",
                "model": "deepseek-r1-distill-qwen-7b-generic-cpu:3",
                "use_rag": True
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/v1/chat", json=payload, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get('response', '')
                        self.log_result("✅ Chat with RAG", f"OK, {len(response_text)} chars", response_text[:100] + '...')
                        return True
                    else:
                        self.log_result("❌ Chat with RAG", f"Status: {response.status}")
                        return False
        except Exception as e:
            self.log_result("❌ Chat with RAG", f"Error: {str(e)}")
            return False

    def log_result(self, test_name, status, details=None):
        """Логирование результата теста"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{test_name}: {status}")
        if details:
            print(f"  Details: {details}")

    async def run_all_tests(self):
        print("🚀 Running comprehensive FastAPI Foundry testing")
        print("=" * 60)
        
        tests = [
            self.test_health,
            self.test_foundry_connection,
            self.test_models_endpoint,
            self.test_rag_search,
            self.test_chat,
            self.test_chat_with_rag
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            result = await test()
            if result:
                passed += 1
            print("-" * 40)
        
        print(f"\n📊 Test Results:")
        print(f"✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")
        
        if passed == total:
            print("🎉 All tests passed successfully!")
        else:
            print("⚠️ Some tests failed")
        
        return self.results

async def main():
    tester = SystemTester()
    results = await tester.run_all_tests()
    
    # Сохранение результатов
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 Results saved to test_results.json")

if __name__ == "__main__":
    asyncio.run(main())ain())(main())))n())))_ascii=False, indent=2)
    
    print(f"\n📄 Results saved to test_results.json")

if __name__ == "__main__":
    asyncio.run(main())ain())(main())))n())))())(main())))n()))))))
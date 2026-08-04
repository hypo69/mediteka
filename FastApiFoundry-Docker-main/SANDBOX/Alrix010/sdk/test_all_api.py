#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI Foundry API Test Suite
# =============================================================================
# Описание:
#   Полное тестирование всех API endpoints
#
# File: test_all_api.py
# Project: Ai Assistant (Docker)
# Version: 0.4.0
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

import requests
import json
import time

class APITester:
    def __init__(self, base_url="http://localhost:9696"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results = []
    
    def test_endpoint(self, method, endpoint, data=None, params=None, description=""):
        """Тестировать один endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, params=params)
            else:
                response = self.session.request(method, url, json=data, params=params)
            
            duration = time.time() - start_time
            
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "duration": round(duration * 1000, 2),  # ms
                "description": description
            }
            
            try:
                result["response"] = response.json()
            except:
                result["response"] = response.text[:200]
            
            self.results.append(result)
            
            status_icon = "✅" if result["success"] else "❌"
            print(f"{status_icon} {method.upper()} {endpoint} - {response.status_code} ({result['duration']}ms)")
            
            if not result["success"]:
                print(f"   Error: {result['response']}")
            
            return result
            
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method.upper(),
                "status_code": 0,
                "success": False,
                "duration": 0,
                "description": description,
                "error": str(e)
            }
            self.results.append(result)
            print(f"❌ {method.upper()} {endpoint} - Connection Error: {e}")
            return result
    
    def run_all_tests(self):
        """Запустить все тесты"""
        print("🧪 FastAPI Foundry API Test Suite")
        print("=" * 60)
        
        # 1. Health endpoints
        print("\n📊 Health & Status:")
        self.test_endpoint("GET", "/api/v1/health", description="System health check")
        
        # 2. Models endpoints
        print("\n🤖 Models:")
        self.test_endpoint("GET", "/api/v1/models", description="List available models")
        self.test_endpoint("GET", "/api/v1/models/connected", description="List connected models")
        self.test_endpoint("GET", "/api/v1/models/providers", description="List model providers")
        self.test_endpoint("POST", "/api/v1/models/health-check", description="Check models health")
        
        # 3. Generation endpoints
        print("\n✍️ Text Generation:")
        self.test_endpoint("POST", "/api/v1/generate", {
            "prompt": "Hello, how are you?",
            "max_tokens": 50,
            "use_rag": False
        }, description="Simple text generation")
        
        self.test_endpoint("POST", "/api/v1/batch-generate", {
            "prompts": ["Hello", "Hi there"],
            "max_tokens": 20,
            "use_rag": False
        }, description="Batch text generation")
        
        # 4. RAG endpoints
        print("\n🔍 RAG System:")
        self.test_endpoint("POST", "/api/v1/rag/search", {
            "query": "FastAPI installation",
            "top_k": 3
        }, description="RAG search")
        
        self.test_endpoint("POST", "/api/v1/rag/reload", description="Reload RAG index")
        
        # 5. Configuration endpoints
        print("\n⚙️ Configuration:")
        self.test_endpoint("GET", "/api/v1/config", description="Get configuration")
        
        # 6. Foundry management
        print("\n🏭 Foundry Management:")
        self.test_endpoint("GET", "/api/v1/foundry/status", description="Foundry status")
        self.test_endpoint("GET", "/api/v1/foundry/models/loaded", description="Loaded Foundry models")
        
        # 7. Examples
        print("\n📝 Examples:")
        self.test_endpoint("GET", "/api/v1/examples/list", description="List examples")
        self.test_endpoint("POST", "/api/v1/examples/run", {
            "example_type": "client"
        }, description="Run example")
        
        # 8. Logs
        print("\n📋 Logs:")
        self.test_endpoint("GET", "/logs/recent", description="Recent logs")
        
        # 9. Static files
        print("\n🌐 Web Interface:")
        self.test_endpoint("GET", "/", description="Main web interface")
        self.test_endpoint("GET", "/docs", description="API documentation")
        
        # 10. Chat endpoints
        print("\n💬 Chat:")
        self.test_endpoint("POST", "/api/v1/chat/message", {
            "message": "Hello",
            "session_id": "test-session"
        }, description="Send chat message")
        
        self.test_endpoint("GET", "/api/v1/chat/history", 
                          params={"session_id": "test-session"}, 
                          description="Get chat history")
        
        # Результаты
        self.print_summary()
    
    def print_summary(self):
        """Вывести сводку результатов"""
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        
        print(f"Total endpoints tested: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        print(f"Success rate: {(successful/total*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ Failed endpoints:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['method']} {result['endpoint']} ({result['status_code']})")
        
        # Самые медленные endpoints
        slow_endpoints = sorted(self.results, key=lambda x: x["duration"], reverse=True)[:5]
        print(f"\n⏱️ Slowest endpoints:")
        for result in slow_endpoints:
            if result["success"]:
                print(f"  - {result['endpoint']}: {result['duration']}ms")
        
        print(f"\n🎯 API Health: {'GOOD' if successful/total > 0.8 else 'NEEDS ATTENTION'}")

def main():
    """Запустить все тесты"""
    tester = APITester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
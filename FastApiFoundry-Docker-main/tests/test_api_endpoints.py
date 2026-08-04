import requests
import json
import time
import os
try:
    from dotenv import load_dotenv
    load_dotenv()  # Загрузит .env из корня, если запустить тест напрямую
except ImportError:
    pass

"""
Проверка доступности и задержки (latency) REST API эндпоинтов.
Base URL: http://localhost:9696/api/v1
"""

BASE_URL = "http://localhost:9696/api/v1"
API_KEY = os.getenv("API_KEY", "your_default_test_key")

def test_endpoint(name, path, payload):
    url = f"{BASE_URL}{path}"
    headers = {"X-API-Key": API_KEY}
    print(f"--- Тестирование: {name} ---")
    try:
        # requests автоматически замеряет время до получения заголовков в response.elapsed
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        latency_ms = response.elapsed.total_seconds() * 1000
        
        if response.status_code == 200:
            print(f"✅ Статус: 200 OK")
            print(f"⏱️  Задержка: {latency_ms:.2f} ms")
            print(f"📝 Фрагмент ответа: {json.dumps(response.json(), indent=2)[:150]}...")
            return True
        else:
            print(f"❌ Ошибка! Статус: {response.status_code}")
            print(f"⚠️  Детали: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"🚨 Ошибка запроса: {e}")
        return False

def main():
    tests = [
        {
            "name": "POST /generate",
            "path": "/generate",
            "payload": {"prompt": "Health check", "model": "foundry::qwen3-0.6b", "max_tokens": 10}
        },
        {
            "name": "POST /chat",
            "path": "/chat",
            "payload": {"message": "Ping system", "model": "foundry::qwen3-0.6b"}
        },
        {
            "name": "POST /rag/search",
            "path": "/rag/search",
            "payload": {"query": "api documentation", "top_k": 1}
        }
    ]

    print(f"🚀 Запуск тестов API на {BASE_URL}\n")
    results = []
    for t in tests:
        results.append(test_endpoint(t["name"], t["path"], t["payload"]))
        print("-" * 40)

    if all(results):
        print("\n🎯 Итог: Все системы работают в пределах нормы.")
    else:
        print("\n⚠️ Итог: Обнаружены сбои или недоступность эндпоинтов.")
        exit(1)

if __name__ == "__main__":
    main()
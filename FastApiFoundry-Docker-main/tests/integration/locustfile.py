# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Нагрузочное тестирование API (Locust)
# =============================================================================
# Описание:
#   Сценарий имитации пользовательской нагрузки на сервер Ai Assistant.
#   Проверяет стабильность эндпоинтов генерации и здоровья под нагрузкой.
#   Для имитации 50 пользователей запустите: 
#   locust -f tests/integration/locustfile.py -u 50 -r 10 --host http://localhost:9696
# Запуск:
#   locust -f tests/integration/locustfile.py --host http://localhost:9696
# =============================================================================

from locust import HttpUser, task, between
import random

class Ai AssistantUser(HttpUser):
    """Имитация поведения пользователя системы Ai Assistant."""
    
    # Ожидание между задачами от 1 до 5 секунд
    wait_time = between(1, 5)

    def on_start(self):
        """Действия при старте сессии пользователя."""
        self.client.headers.update({"X-API-Key": "test_key_if_needed"})

    @task(3)
    def check_health(self):
        """Частая проверка статуса системы."""
        self.client.get("/api/v1/health")

    @task(1)
    def list_models(self):
        """Просмотр списка доступных моделей."""
        self.client.get("/api/v1/models")

    @task(2)
    def generate_simple_prompt(self):
        """Имитация запроса на генерацию текста."""
        prompts = [
            "What is Ai Assistant?",
            "How to install FastAPI Foundry?",
            "Tell me about RAG systems",
            "Ping"
        ]
        payload = {
            "prompt": random.choice(prompts),
            "model": "foundry::default",
            "max_tokens": 20
        }
        with self.client.post("/api/v1/generate", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 503:
                response.failure("Service busy (model loading or queue full)")
            else:
                response.failure(f"Unexpected status: {response.status_code}")

    @task(2)
    def generate_streaming_prompt(self):
        """Имитация запроса на потоковую генерацию текста."""
        payload = {
            "prompt": "Write a short story about a robot learning to paint.",
            "model": "foundry::default",
            "stream": True
        }
        # Используем stream=True для корректной обработки Server-Sent Events (SSE)
        with self.client.post("/api/v1/generate", json=payload, stream=True, catch_response=True) as response:
            if response.status_code == 200:
                # Итерируемся по строкам для имитации реального потребления чанков пользователем
                for line in response.iter_lines():
                    if line:
                        pass
                response.success()
            else:
                response.failure(f"Streaming request failed: {response.status_code}")
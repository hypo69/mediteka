#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: RAG System Client Example
# =============================================================================
# Описание:
#   Пример клиента для работы с RAG системой FastAPI Foundry
#   Демонстрирует поиск контекста и генерацию с RAG
#
# File: example_rag_client.py
# Project: Ai Assistant
# Module: FastApiFoundry
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
from example_client import FastAPIFoundryClient

async def demo_rag_system():
    """Демонстрация RAG системы"""
    
    async with FastAPIFoundryClient(
        base_url="http://localhost:9696",
        api_key=None  # API ключ отключен в .env
    ) as client:
        
        print("🔍 FastAPI Foundry - RAG System Demo")
        print("=" * 60)
        
        # 1. Проверка статуса RAG системы
        print("\n1️⃣ RAG System Status:")
        try:
            health = await client.get_health()
            rag_status = health.get('rag_status', 'unknown')
            rag_chunks = health.get('rag_chunks', 0)
            
            print(f"  Status: {rag_status}")
            print(f"  Indexed chunks: {rag_chunks}")
            
            if rag_status != 'ready':
                print("⚠️ RAG система не готова. Проверьте:")
                print("   - Запущен ли rag_indexer.py")
                print("   - Существует ли директория rag_index/")
                print("   - Установлены ли зависимости для RAG")
                return
                
        except Exception as e:
            print(f"❌ Ошибка проверки статуса: {e}")
            return
        
        # 2. Поиск в RAG индексе
        print("\n2️⃣ RAG Search Examples:")
        
        search_queries = [
            "How to install FastAPI Foundry?",
            "Docker configuration",
            "API endpoints",
            "RAG system setup",
            "MCP integration"
        ]
        
        for query in search_queries:
            print(f"\n🔍 Поиск: '{query}'")
            try:
                # Поиск через RAG API
                search_result = await client.make_request(
                    "POST", 
                    "/api/v1/rag/search",
                    json={"query": query, "top_k": 3}
                )
                
                if search_result.get('success'):
                    results = search_result.get('results', [])
                    print(f"  Найдено результатов: {len(results)}")
                    
                    for i, result in enumerate(results, 1):
                        print(f"    {i}. {result.get('source', 'Unknown source')}")
                        print(f"       Score: {result.get('score', 0):.3f}")
                        print(f"       Text: {result.get('text', '')[:100]}...")
                        print()
                else:
                    print(f"  ❌ Ошибка поиска: {search_result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"  ❌ Ошибка запроса: {e}")
        
        # 3. Генерация с RAG контекстом
        print("\n3️⃣ RAG-Enhanced Generation:")
        
        rag_questions = [
            "Как установить FastAPI Foundry?",
            "Как настроить Docker для проекта?",
            "Какие есть API endpoints?",
            "Как работает MCP интеграция?"
        ]
        
        for question in rag_questions:
            print(f"\n❓ Вопрос: '{question}'")
            try:
                # Генерация с RAG
                response = await client.generate_text(
                    prompt=question,
                    use_rag=True,
                    max_tokens=200,
                    temperature=0.7
                )
                
                if response.get('success'):
                    print("✅ Ответ с RAG контекстом:")
                    print(f"   {response.get('response', 'Нет ответа')}")
                    
                    # Показать использованные источники
                    if 'rag_sources' in response:
                        sources = response['rag_sources']
                        print(f"   📚 Источники ({len(sources)}):")
                        for source in sources:
                            print(f"     - {source}")
                else:
                    print(f"❌ Ошибка генерации: {response.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"❌ Ошибка запроса: {e}")
        
        # 4. Сравнение с обычной генерацией
        print("\n4️⃣ Comparison: RAG vs Normal Generation:")
        
        test_question = "Как запустить FastAPI Foundry в Docker?"
        
        print(f"\n🔄 Тестовый вопрос: '{test_question}'")
        
        # Обычная генерация
        print("\n📝 Обычная генерация (без RAG):")
        try:
            normal_response = await client.generate_text(
                prompt=test_question,
                use_rag=False,
                max_tokens=150
            )
            
            if normal_response.get('success'):
                print(f"   {normal_response.get('response', 'Нет ответа')}")
            else:
                print(f"   ❌ Ошибка: {normal_response.get('error', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # RAG генерация
        print("\n🔍 Генерация с RAG:")
        try:
            rag_response = await client.generate_text(
                prompt=test_question,
                use_rag=True,
                max_tokens=150
            )
            
            if rag_response.get('success'):
                print(f"   {rag_response.get('response', 'Нет ответа')}")
                
                if 'rag_sources' in rag_response:
                    sources = rag_response['rag_sources']
                    print(f"   📚 Источники: {', '.join(sources)}")
            else:
                print(f"   ❌ Ошибка: {rag_response.get('error', 'Unknown')}")
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        # 5. RAG статистика
        print("\n5️⃣ RAG Statistics:")
        try:
            # Получить статистику через health endpoint
            health = await client.get_health()
            
            print(f"  📊 Индексированных чанков: {health.get('rag_chunks', 0)}")
            print(f"  📁 Директория индекса: {health.get('rag_index_path', 'Unknown')}")
            print(f"  🔧 RAG модель: {health.get('rag_model', 'Unknown')}")
            
        except Exception as e:
            print(f"  ❌ Ошибка получения статистики: {e}")
        
        # 6. Полезные команды
        print("\n6️⃣ Useful RAG Commands:")
        print("📋 Создание RAG индекса:")
        print("   python rag_indexer.py")
        print()
        print("🔍 Поиск через API:")
        print("   curl -X POST http://localhost:9696/api/v1/rag/search \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"query\": \"installation\", \"top_k\": 5}'")
        print()
        print("🤖 Генерация с RAG:")
        print("   curl -X POST http://localhost:9696/api/v1/generate \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"prompt\": \"How to install?\", \"use_rag\": true}'")
        print()
        print("📊 Проверка статуса RAG:")
        print("   curl http://localhost:9696/api/v1/health")
        print()
        print("🔧 Переиндексация:")
        print("   python rag_indexer.py --rebuild")
        
        print("\n" + "=" * 60)
        print("🎉 RAG System Demo Complete!")
        print("📚 RAG система позволяет получать более точные ответы")
        print("    используя контекст из документации проекта")

if __name__ == "__main__":
    asyncio.run(demo_rag_system())
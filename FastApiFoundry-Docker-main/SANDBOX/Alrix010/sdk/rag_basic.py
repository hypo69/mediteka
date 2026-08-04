# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: RAG Basic Example
# =============================================================================
# Описание:
#   Базовый пример работы с RAG системой FastAPI Foundry
#   Показывает настройку, поиск и генерацию с контекстом
#
# Примеры:
#   python rag_basic.py
#
# File: rag_basic.py
# Project: Ai Assistant (Docker)
# Version: 0.4.0
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

import requests
import json
from pathlib import Path

API_BASE = "http://localhost:9696/api/v1"

def setup_rag():
    """Настройка RAG системы"""
    print("🔧 Настройка RAG системы...")
    
    config = {
        "enabled": True,
        "index_dir": "./rag_index",
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "chunk_size": 1000,
        "top_k": 5
    }
    
    try:
        response = requests.put(f"{API_BASE}/rag/config", json=config)
        data = response.json()
        
        if data.get("success"):
            print("✅ RAG система настроена успешно")
            return True
        else:
            print(f"❌ Ошибка настройки: {data.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def check_rag_status():
    """Проверка статуса RAG системы"""
    print("\n📊 Проверка статуса RAG...")
    
    try:
        response = requests.get(f"{API_BASE}/rag/status")
        data = response.json()
        
        if data.get("success"):
            print(f"Status: {'✅ Enabled' if data['enabled'] else '❌ Disabled'}")
            print(f"Model: {data['model']}")
            print(f"Chunks: {data['total_chunks']}")
            print(f"Index: {data['index_dir']}")
        else:
            print(f"❌ Ошибка: {data.get('error')}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def search_rag(query):
    """Поиск в RAG системе"""
    print(f"\n🔍 Поиск: '{query}'")
    
    try:
        response = requests.post(
            f"{API_BASE}/rag/search",
            json={"query": query, "top_k": 3}
        )
        data = response.json()
        
        if data.get("success"):
            results = data.get("results", [])
            print(f"Найдено {len(results)} результатов:")
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. Score: {result['score']:.3f}")
                print(f"   Content: {result['content'][:150]}...")
        else:
            print(f"❌ Ошибка поиска: {data.get('error')}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def generate_with_context(question):
    """Генерация ответа с RAG контекстом"""
    print(f"\n🤖 Генерация ответа на: '{question}'")
    
    # 1. Поиск контекста
    try:
        search_response = requests.post(
            f"{API_BASE}/rag/search",
            json={"query": question, "top_k": 2}
        )
        
        context = ""
        if search_response.status_code == 200:
            search_data = search_response.json()
            if search_data.get("success"):
                results = search_data.get("results", [])
                context = "\n".join([r["content"] for r in results])
        
        # 2. Генерация с контекстом
        prompt = f"""
Контекст из документации:
{context}

Вопрос: {question}

Ответь на вопрос, используя информацию из контекста выше.
"""
        
        generate_response = requests.post(
            f"{API_BASE}/generate",
            json={
                "prompt": prompt,
                "max_tokens": 300,
                "temperature": 0.7
            }
        )
        
        if generate_response.status_code == 200:
            gen_data = generate_response.json()
            if gen_data.get("success"):
                print("💬 Ответ:")
                print(gen_data["content"])
            else:
                print(f"❌ Ошибка генерации: {gen_data.get('error')}")
        else:
            print(f"❌ HTTP Error: {generate_response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    """Основная функция демонстрации RAG"""
    print("🚀 FastAPI Foundry RAG Demo")
    print("=" * 50)
    
    # 1. Настройка RAG
    if not setup_rag():
        print("❌ Не удалось настроить RAG. Проверьте, что сервер запущен.")
        return
    
    # 2. Проверка статуса
    check_rag_status()
    
    # 3. Примеры поиска
    search_queries = [
        "FastAPI configuration",
        "RAG system setup",
        "API endpoints"
    ]
    
    for query in search_queries:
        search_rag(query)
    
    # 4. Генерация с контекстом
    questions = [
        "Как настроить FastAPI Foundry?",
        "Что такое RAG система?"
    ]
    
    for question in questions:
        generate_with_context(question)
    
    print("\n✅ Демонстрация завершена!")

if __name__ == "__main__":
    main()
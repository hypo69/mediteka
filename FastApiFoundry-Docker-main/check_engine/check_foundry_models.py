#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест для проверки моделей в Foundry
"""
import asyncio
import os
from src.models.foundry_client import foundry_client

async def test_foundry_models():
    """Тестирование получения моделей от Foundry"""
    print("🔍 Проверка моделей в Foundry...")
    
    # Проверяем переменную окружения
    foundry_url = os.getenv('FOUNDRY_BASE_URL', 'http://localhost:63995/v1/')
    print(f"🔗 Foundry URL: {foundry_url}")
    
    # Проверяем health
    health = await foundry_client.health_check()
    print(f"💚 Health: {health}")
    
    # Получаем модели
    models_result = await foundry_client.list_available_models()
    print(f"📋 Models result: {models_result}")
    
    if models_result.get('success'):
        models = models_result.get('models', [])
        print(f"✅ Найдено {len(models)} моделей:")
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model.get('id', 'unknown')} - {model.get('object', 'model')}")
    else:
        print(f"❌ Ошибка получения моделей: {models_result.get('error')}")
    
    await foundry_client.close()

if __name__ == "__main__":
    asyncio.run(test_foundry_models())
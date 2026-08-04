# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тест сохранения модели по умолчанию
# =============================================================================
# Описание:
#   Тест для проверки сохранения выбранной модели как модели по умолчанию
#
# File: test_default_model.py
# Project: Ai Assistant (Docker)
# Version: 0.2.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

import requests
import json
import time

def test_default_model_functionality():
    """Тест функциональности модели по умолчанию"""
    base_url = "http://localhost:9696/api/v1"
    
    print("🧪 Тестирование функциональности модели по умолчанию...")
    
    # 1. Получение текущей конфигурации
    print("\n1. Получение текущей конфигурации...")
    try:
        response = requests.get(f"{base_url}/config")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                original_model = data['config']['foundry_ai']['default_model']
                print(f"✅ Текущая модель по умолчанию: {original_model}")
            else:
                print(f"❌ Ошибка: {data.get('error')}")
                return
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # 2. Получение списка доступных моделей
    print("\n2. Получение списка доступных моделей...")
    try:
        response = requests.get(f"{base_url}/foundry/models/loaded")
        if response.status_code == 200:
            models_data = response.json()
            if models_data.get("success") and models_data.get("models"):
                available_models = [m['id'] for m in models_data['models']]
                print(f"✅ Доступные модели: {available_models}")
                
                if not available_models:
                    print("⚠️ Нет доступных моделей для тестирования")
                    return
                    
                # Выбираем первую доступную модель для теста
                test_model = available_models[0]
                print(f"🎯 Используем для теста: {test_model}")
            else:
                print("⚠️ Нет доступных моделей")
                return
        else:
            print(f"❌ Ошибка получения моделей: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка получения моделей: {e}")
        return
    
    # 3. Тест установки новой модели по умолчанию
    print(f"\n3. Установка модели по умолчанию: {test_model}...")
    try:
        # Обновляем конфигурацию
        config = data['config'].copy()
        config['foundry_ai']['default_model'] = test_model
        
        response = requests.post(f"{base_url}/config", 
                               json={"config": config})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Модель по умолчанию обновлена")
            else:
                print(f"❌ Ошибка обновления: {result.get('error')}")
                return
        else:
            print(f"❌ HTTP ошибка при обновлении: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Ошибка при обновлении: {e}")
        return
    
    # 4. Проверка что модель сохранилась
    print("\n4. Проверка сохранения модели...")
    try:
        time.sleep(1)  # Небольшая пауза
        response = requests.get(f"{base_url}/config")
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                current_model = data['config']['foundry_ai']['default_model']
                if current_model == test_model:
                    print(f"✅ Модель по умолчанию корректно сохранена: {current_model}")
                else:
                    print(f"❌ Модель не сохранилась. Ожидалось: {test_model}, получено: {current_model}")
            else:
                print(f"❌ Ошибка при проверке: {data.get('error')}")
        else:
            print(f"❌ HTTP ошибка при проверке: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
    
    # 5. Тест с несуществующей моделью
    print("\n5. Тест с несуществующей моделью...")
    try:
        fake_model = "non-existent-model-12345"
        config = data['config'].copy()
        config['foundry_ai']['default_model'] = fake_model
        
        response = requests.post(f"{base_url}/config", 
                               json={"config": config})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✅ Несуществующая модель сохранена в конфиг: {fake_model}")
                print("   (Система должна показать предупреждение в интерфейсе)")
            else:
                print(f"❌ Ошибка сохранения: {result.get('error')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # 6. Восстановление исходной конфигурации
    print(f"\n6. Восстановление исходной модели: {original_model}...")
    try:
        config = data['config'].copy()
        config['foundry_ai']['default_model'] = original_model
        
        response = requests.post(f"{base_url}/config", 
                               json={"config": config})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Исходная конфигурация восстановлена")
            else:
                print(f"❌ Ошибка восстановления: {result.get('error')}")
        else:
            print(f"❌ HTTP ошибка при восстановлении: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при восстановлении: {e}")
    
    print("\n🎯 Тест завершен!")
    print("\n📋 Проверьте в веб-интерфейсе:")
    print("   1. Откройте http://localhost:9696")
    print("   2. В разделе Chat Settings должен отображаться статус модели")
    print("   3. При выборе модели из Available Models она автоматически сохраняется")
    print("   4. При недоступной модели показывается предупреждение")

if __name__ == "__main__":
    test_default_model_functionality()
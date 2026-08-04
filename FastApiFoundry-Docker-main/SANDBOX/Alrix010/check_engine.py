from sdk import FoundryClient


# Создание клиента
with FoundryClient("http://localhost:9696") as client:
    
    # Проверка здоровья
    health = client.health()
    print(health.get("status"))
    
    # Генерация текста
    response = client.generate("Hello world")
    if response.get("success"):
        print(response.get("content"))
    
    # Чат
    chat_response = client.chat("Hi there!")
    
    # Список моделей
    models = client.list_models()
    
    # RAG поиск
    results = client.rag_search("FastAPI")
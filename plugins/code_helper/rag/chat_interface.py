import asyncio
from pathlib import Path
from plugins.code_helper.rag.engine import FaissEngine
from src.ai.gemini.generative_ai import GoogleGenerativeAI
from src.logger import logger

class CodeHelperChat:
    def __init__(self):
        self.rag_dir = Path(__file__).parent.parent / "rag"
        self.engine = FaissEngine(self.rag_dir)
        self.model = GoogleGenerativeAI(api_key_names=['fmashulia'])
        
    async def chat(self, query: str):
        print(f"\nЗапрос: {query}")
        
        # 1. Поиск контекста
        context_data = await self.engine.search(query, top_k=3)
        
        if not context_data:
            return "Не удалось найти подходящий контекст в кодовой базе."
            
        context_text = "\n\n".join([f"Источник: {d['data']['meta']['path']}\n{d['data']['text']}" for d in context_data])
        
        # 2. Формирование промпта
        prompt = f"""Ты — помощник разработчика Code Helper.
Используй следующий контекст из кодовой базы проекта, чтобы ответить на вопрос пользователя.
Если ответ нельзя найти в контексте, скажи об этом.

КОНТЕКСТ:
{context_text}

ВОПРОС:
{query}
"""
        
        # 3. Получение ответа
        # Используем метод chat у модели, если он есть, или генерируем через модель
        # Для простоты используем метод генерации из модели
        response = await self.model._chat.send_message_async(prompt)
        return response.text

async def main():
    helper = CodeHelperChat()
    while True:
        query = input("\nВведите вопрос (или 'exit' для выхода): ")
        if query.lower() == 'exit':
            break
        response = await helper.chat(query)
        print(f"\nОтвет: {response}")

if __name__ == "__main__":
    asyncio.run(main())

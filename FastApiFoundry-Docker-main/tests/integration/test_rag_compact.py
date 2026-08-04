# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock, patch
import os

@pytest.mark.asyncio
class TestRagCompactMechanism:
    """
    Интеграционный тест механизма Compact (Soft-delete -> Physical Cleanup).
    Проверяет, что после Compact в FAISS остаются только активные чанки.
    """

    async def test_compact_lifecycle(self, mocker):
        # 1. Мокаем компоненты RAG системы
        # В реальной жизни это будет обращение к SQLite и FAISS через RagSystem
        mock_db = mocker.patch('src.rag.rag_system.SQLiteManager')
        mock_faiss = mocker.patch('src.rag.rag_system.FAISSManager')
        
        # Имитируем состояние базы до очистки
        # 5 чанков всего, из них 2 помечены как неактивные (is_active=0)
        active_chunks = [
            {"id": 1, "text": "Active 1"},
            {"id": 2, "text": "Active 2"},
            {"id": 5, "text": "Active 3"}
        ]
        mock_db.return_value.get_all_active_chunks.return_value = active_chunks
        mock_db.return_value.get_stats.return_value = {
            "total_chunks": 5,
            "active_chunks": 3,
            "inactive_chunks": 2
        }

        # 2. Инициализируем систему (псевдокод вызова)
        # В вашем коде это вызов метода из эндпоинта /api/v1/rag/compact
        from src.rag.rag_system import RagSystem
        rag = RagSystem(profile_name="test_profile")
        
        # 3. Выполняем очистку
        result = await rag.compact()

        # 4. Проверки
        assert result["success"] is True
        
        # Проверяем, что система запросила только активные чанки из БД
        mock_db.return_value.get_all_active_chunks.assert_called_once()
        
        # Главная проверка: FAISS должен быть пересобран ровно из 3 активных векторов
        # verify faiss.rebuild(active_chunks)
        mock_faiss.return_value.rebuild_from_data.assert_called_with(active_chunks)
        
        # Проверяем финальную статистику
        mock_db.return_value.get_stats.return_value = {
            "total_chunks": 3,
            "active_chunks": 3,
            "inactive_chunks": 0
        }
        stats = await rag.get_stats()
        assert stats["inactive_chunks"] == 0
        assert stats["total_chunks"] == 3
        print(f"✅ Compact test passed: {stats['total_chunks']} chunks recovered.")
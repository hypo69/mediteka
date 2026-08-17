# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты RAG сериалов и агрегации верхнего уровня
# =============================================================================
# Описание:
#   Тестирование агрегации информации о сезонах и сериях на уровне сериала,
#   проверка фильтрации RAG-индекса и корректности выдачи типов медиа.
#
# File: tests/test_media_rag_series.py
# Project: gemini-simplechat
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import pytest
from unittest.mock import Mock, patch

from plugins.media_organizer.core.media_rag import _record_to_text, build_media_rag
from plugins.media_organizer.core.media_rag_functions import get_media_card, search_media


class TestMediaRagSeriesAggregation:
    """Тесты агрегации сериалов и RAG-индексации."""

    def test_record_to_text_movie(self):
        """Тест сериализации фильма в текст."""
        movie_record = {
            'title': 'Интерстеллар',
            'title_ru': 'Интерстеллар',
            'title_orig': 'Interstellar',
            'media_type': 'movie',
            'year': 2014,
            'main_category': 'Фантастика',
            'country': 'США',
            'genres': ['Фантастика', 'Драма'],
            'directors': ['Кристофер Нолан'],
            'cast': ['Мэттью Макконахи'],
            'plot': 'Исследователи отправляются через червоточину в космосе.',
        }
        text = _record_to_text(movie_record)
        assert 'Интерстеллар' in text
        assert 'Тип: Фильм' in text
        assert 'Кристофер Нолан' in text
        assert 'червоточину' in text

    def test_record_to_text_series_with_seasons(self):
        """Тест сериализации сериала с прикрепленными данными сезонов."""
        series_record = {
            'title': 'Остаться в живых',
            'title_ru': 'Остаться в живых',
            'title_orig': 'Lost',
            'media_type': 'series',
            'year': 2004,
            'num_of_seasons': 6,
            'main_category': 'Детектив',
            'genres': ['Детектив', 'Драма'],
            'plot': 'Самолет терпит крушение на загадочном острове.',
        }
        seasons_data = [
            {
                'title': 'Сезон 1',
                'plot': 'Выжившие обустраивают лагерь и находят люк.',
                'final_verdict': 'Культовое начало.',
                'episodes': [
                    {'title': 'S01E01 Пилот', 'plot': 'Крушение рейса 815'}
                ]
            },
            {
                'title': 'Сезон 2',
                'plot': 'Открытие станции Лебедь и знакомство с Другими.',
                'final_verdict': 'Отличное продолжение.',
                'episodes': []
            }
        ]
        text = _record_to_text(series_record, seasons_data=seasons_data)
        assert 'Остаться в живых' in text
        assert 'Тип: Сериал' in text
        assert 'Количество сезонов: 6' in text
        assert 'Содержание сезонов:' in text
        assert 'Выжившие обустраивают лагерь' in text
        assert 'Открытие станции Лебедь' in text
        assert 'S01E01 Пилот' in text

    def test_build_media_rag_filters_child_records(self):
        """Тест того, что build_media_rag индексирует только фильмы и сериалы, не создавая документы для сезонов/эпизодов."""
        mock_records = [
            {'id': 1, 'title': 'Фильм 1', 'media_type': 'movie', 'disk_name': 'ДИСК 1', 'parent_id': 0},
            {'id': 2, 'title': 'Сериал 1', 'media_type': 'series', 'disk_name': 'ДИСК 1', 'parent_id': 0, 'num_of_seasons': 2},
            {'id': 3, 'title': 'Сериал 1 (сезон 1)', 'media_type': 'season', 'disk_name': 'ДИСК 1', 'parent_id': 2, 'plot': 'Сюжет сезона 1'},
            {'id': 4, 'title': 'Сериал 1 (сезон 2)', 'media_type': 'season', 'disk_name': 'ДИСК 1', 'parent_id': 2, 'plot': 'Сюжет сезона 2'},
            {'id': 5, 'title': 'Сериал 1 S01E01', 'media_type': 'episode', 'disk_name': 'ДИСК 1', 'parent_id': 3, 'plot': 'Серия 1'},
        ]

        mock_db = Mock()
        mock_db.export_all.return_value = mock_records

        mock_rag_instance = Mock()
        mock_rag_instance.add_documents = Mock(return_value=2)
        mock_rag_instance.clear = Mock()

        with patch('plugins.media_organizer.core.media_rag.MediaDatabase', return_value=mock_db), \
             patch('plugins.media_organizer.core.media_rag.GeminiRAG', return_value=mock_rag_instance):
            build_media_rag(api_key='fake_api_key')

        assert mock_rag_instance.add_documents.called
        docs_passed = mock_rag_instance.add_documents.call_args[0][0]

        assert len(docs_passed) == 2
        titles = [d['meta']['title'] for d in docs_passed]
        assert 'Фильм 1' in titles
        assert 'Сериал 1' in titles
        assert 'Сериал 1 (сезон 1)' not in titles
        assert 'Сериал 1 S01E01' not in titles

        series_doc = next(d for d in docs_passed if d['meta']['title'] == 'Сериал 1')
        assert 'Сюжет сезона 1' in series_doc['text']
        assert 'Сюжет сезона 2' in series_doc['text']
        assert 'Серия 1' in series_doc['text']
        assert series_doc['meta']['media_type'] == 'series'
        assert 'type' not in series_doc['meta']

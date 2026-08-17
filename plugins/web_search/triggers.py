# -*- coding: utf-8 -*-
"""Модуль триггеров распознавания запросов для веб-поиска."""

import re
from typing import Tuple

# Явные ключевые фразы, требующие поиска в интернете
_WEB_TRIGGERS = [
    "поищи в интернете", "найди в интернете", "посмотри в интернете",
    "поищи в сети", "найди в сети", "посмотри в сети",
    "посмотри на форумах", "поищи на форумах", "погугли", "загугли",
    "найди информацию о", "интернет поиск", "поиск в интернете",
    "в интернете", "онлайн поиск", "найди онлайн", "в вебе"
]

def is_web_search_query(message: str) -> bool:
    """Определяет, содержит ли сообщение явный запрос на поиск в интернете."""
    if not message:
        return False
    low = message.lower()
    return any(trig in low for trig in _WEB_TRIGGERS)

def extract_clean_query(message: str) -> str:
    """Очищает запрос от служебных фраз триггеров веб-поиска."""
    clean = message
    for trig in _WEB_TRIGGERS:
        pattern = re.compile(re.escape(trig), re.IGNORECASE)
        clean = pattern.sub("", clean)
    # Удаляем лишние пробелы и знаки препинания по краям
    return clean.strip(" ,.?!:;\"'")

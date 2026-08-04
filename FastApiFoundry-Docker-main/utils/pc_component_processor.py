# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Обработка и фильтрация компонентов компьютера
# =============================================================================
# Описание:
#   Модуль для анализа JSON данных о компонентах ПК, классификации типов сборок
#   и формирования структурированных ответов на русском языке.
#   Включает логику исключения запрещенных брендов и парсинг готовых сборок.
#
# Примеры:
#   >>> processor = PCComponentProcessor()
#   >>> result = processor.execute(input_data)
#
# File: utils/pc_component_processor.py
# Project: Ai Assistant (Docker)
# Package: utils
# Module: pc_component_processor
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from src import gs
from src.logger import logger
from src.utils.printer import pprint
from src.utils.json import j_loads, j_dumps
from typing import Optional, List, Dict

class PCComponentProcessor:
    """Класс для обработки и нормализации данных о компонентах ПК

    Attributes:
        banned_brands (List[str]): Список брендов, подлежащих удалению.
    """

    def __init__(self) -> None:
        """Инициализация экземпляра класса."""
        # Инициализация списка запрещенных брендов (согласно инструкции)
        self.banned_brands: List[str] = ["IVORY", "מור לוי", "KSP", "k.s.p.", "grandadvance", "גנדאдуванс"]

    def execute(self, data_path: str) -> Optional[Dict]:
        """Запуск процесса обработки данных

        Args:
            data_path (str): Путь к файлу с входными данными.

        Returns:
            Optional[Dict]: Обработанный JSON ответ или None.
        """
        # Чтение входных данных через стандартную функцию
        data: dict = j_loads(data_path)

        # Проверка наличия данных для предотвращения обработки пустого входа
        # Verification of data presence to prevent empty input processing
        if not data:
            return None

        # Получение временной метки начала процесса
        # Определение текущего времени через глобальные настройки
        start_time = gs.now()
        
        result: Dict = self._process_items(data)
        
        # Вывод результата через pprint (запрет на print)
        pprint(result)
        return result

    def _process_items(self, data: Dict) -> Dict:
        """Внутренняя обработка элементов данных

        Args:
            data (Dict): Словарь данных.

        Returns:
            Dict: Результат нормализации.
        """
        processed_components: List[Dict] = []

        # Проверка структуры входного словаря
        # Validation of the 'items' key existence within the data structure
        if 'items' not in data:
            return {"error": "Missing items"}

        for item in data.get('items', []):
            # Фильтрация названия компонента от нежелательных брендов
            # Filtration of the component name to remove banned brands
            item['name'] = self._filter_brands(item.get('name', ''))

            # Идентификация параметров сборки для распаковки
            # Identification of build parameters for unpacking logic
            if 'build_params' in item:
                # Извлечение компонентов из готовой сборки
                extracted = self._unpack_build(item)
                processed_components.extend(extracted)
                continue

            processed_components.append(item)

        return {"components": processed_components}

    def _filter_brands(self, text: str) -> str:
        """Фильтрация текста от упоминания компаний

        Args:
            text (str): Исходный текст.

        Returns:
            str: Очищенный текст.
        """
        # Проверка пустого входящего текста
        # Return of empty string for None values
        if not text:
            return ""

        clean_text: str = text
        for brand in self.banned_brands:
            # Замена найденных брендов на пустую строку
            # Replacement of the banned brand occurrences
            clean_text = clean_text.replace(brand, "")
        
        return clean_text.strip()
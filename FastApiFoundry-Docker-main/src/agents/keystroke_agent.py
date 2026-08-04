# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Keystroke Agent — идентификация пользователя по клавиатурному почерку
# =============================================================================
# Description:
#   Агент анализирует паттерны нажатий клавиш и идентифицирует пользователей
#   с помощью RandomForestClassifier (scikit-learn).
#
#   Tools:
#     - train_model   : обучить модель на данных сессий нажатий клавиш
#     - predict_user  : идентифицировать пользователя по новой сессии
#     - get_model_info: получить статус и метрики обученной модели
#
#   Формат данных сессии: список длительностей нажатий клавиш в мс.
#   Пример: [95.2, 110.5, 88.3, 102.1, ...]
#
# File: src/agents/keystroke_agent.py
# Project: Ai Assistant (Docker)
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import logging
from typing import Any, Dict, List, Optional

from .base import BaseAgent, ToolDefinition

logger = logging.getLogger(__name__)


class KeystrokeAgent(BaseAgent):
    """Агент идентификации пользователя по клавиатурному почерку.

    Хранит обученную ML-модель в памяти между вызовами инструментов.
    Использует RandomForestClassifier из scikit-learn.
    """

    name = "keystroke"
    description = "Идентифицирует пользователей по паттернам нажатий клавиш (ML, scikit-learn)"

    def __init__(self, foundry_client):
        super().__init__(foundry_client)
        self._model: Any = None
        self._scaler: Any = None
        self._accuracy: Optional[float] = None
        self._trained_users: List[str] = []
        self._train_samples: int = 0

    @property
    def tools(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="train_model",
                description=(
                    "Обучить модель идентификации на данных нескольких пользователей. "
                    "Принимает словарь {username: [[сессия1], [сессия2], ...]}, "
                    "где каждая сессия — список длительностей нажатий клавиш в мс."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "users_data": {
                            "type": "object",
                            "description": (
                                "Словарь: ключ — имя пользователя, "
                                "значение — список сессий. "
                                "Каждая сессия — список чисел (мс). "
                                "Пример: {\"alice\": [[95,110,88], [102,91,115]], "
                                "\"bob\": [[140,155,130], [148,162,138]]}"
                            )
                        }
                    },
                    "required": ["users_data"]
                }
            ),
            ToolDefinition(
                name="predict_user",
                description=(
                    "Идентифицировать пользователя по новой сессии нажатий клавиш. "
                    "Требует предварительного обучения через train_model."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "session": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Список длительностей нажатий клавиш в мс"
                        }
                    },
                    "required": ["session"]
                }
            ),
            ToolDefinition(
                name="get_model_info",
                description="Получить статус модели: обучена ли, точность, список пользователей",
                parameters={"type": "object", "properties": {}}
            ),
        ]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Выполнить инструмент агента.

        Args:
            name (str): Имя инструмента.
            arguments (Dict[str, Any]): Аргументы вызова.

        Returns:
            str: Результат выполнения.
        """
        if name == "train_model":
            return self._train_model(arguments)
        if name == "predict_user":
            return self._predict_user(arguments)
        if name == "get_model_info":
            return self._get_model_info()
        return f"❌ Неизвестный инструмент: {name}"

    def _extract_features(self, session: List[float]) -> List[float]:
        """Извлечь признаки из одной сессии нажатий клавиш.

        Признаки: среднее, стандартное отклонение, медиана, мин, макс,
        межквартильный размах (IQR).

        Args:
            session (List[float]): Длительности нажатий в мс.

        Returns:
            List[float]: Вектор из 6 признаков.
        """
        import statistics

        if not session:
            return [0.0] * 6

        sorted_s = sorted(session)
        n = len(sorted_s)
        mean = sum(sorted_s) / n
        variance = sum((x - mean) ** 2 for x in sorted_s) / n
        std = variance ** 0.5
        median = sorted_s[n // 2] if n % 2 else (sorted_s[n // 2 - 1] + sorted_s[n // 2]) / 2
        q1 = sorted_s[n // 4]
        q3 = sorted_s[(3 * n) // 4]
        iqr = q3 - q1

        return [mean, std, median, sorted_s[0], sorted_s[-1], iqr]

    def _train_model(self, args: Dict[str, Any]) -> str:
        """Обучить RandomForestClassifier на данных пользователей.

        Args:
            args: users_data — {username: [[сессия], ...]}.

        Returns:
            str: Результат обучения с метриками.
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import accuracy_score
        except ImportError:
            return "❌ scikit-learn не установлен. Выполните: pip install scikit-learn"

        users_data: Dict[str, List] = args.get("users_data", {})

        if not users_data or len(users_data) < 2:
            return "❌ Нужны данные минимум для 2 пользователей"

        X: List[List[float]] = []
        y: List[str] = []

        for username, sessions in users_data.items():
            if not sessions:
                continue
            for session in sessions:
                if not session:
                    continue
                features = self._extract_features([float(v) for v in session])
                X.append(features)
                y.append(username)

        if len(X) < 4:
            return "❌ Недостаточно данных для обучения (нужно минимум 4 сессии)"

        # Split — если данных мало, уменьшаем test_size
        test_size = 0.3 if len(X) >= 10 else 0.2
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if len(X) >= 6 else None
        )

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train_s, y_train)

        predictions = model.predict(X_test_s)
        accuracy = accuracy_score(y_test, predictions)

        self._model = model
        self._scaler = scaler
        self._accuracy = accuracy
        self._trained_users = list(users_data.keys())
        self._train_samples = len(X)

        return json.dumps({
            "status": "trained",
            "accuracy": round(accuracy, 4),
            "users": self._trained_users,
            "total_sessions": self._train_samples,
            "train_size": len(X_train),
            "test_size": len(X_test),
            "features": ["mean_ms", "std_ms", "median_ms", "min_ms", "max_ms", "iqr_ms"]
        }, ensure_ascii=False)

    def _predict_user(self, args: Dict[str, Any]) -> str:
        """Идентифицировать пользователя по сессии нажатий.

        Args:
            args: session — список длительностей нажатий в мс.

        Returns:
            str: Предсказанный пользователь и вероятности.
        """
        if self._model is None or self._scaler is None:
            return "❌ Модель не обучена. Сначала вызовите train_model"

        session = args.get("session", [])
        if not session:
            return "❌ Пустая сессия"

        features = self._extract_features([float(v) for v in session])
        scaled = self._scaler.transform([features])
        predicted = self._model.predict(scaled)[0]

        probas = self._model.predict_proba(scaled)[0]
        classes = self._model.classes_
        proba_map = {cls: round(float(p), 4) for cls, p in zip(classes, probas)}

        return json.dumps({
            "predicted_user": predicted,
            "confidence": round(float(max(probas)), 4),
            "probabilities": proba_map,
            "session_features": {
                "mean_ms": round(features[0], 2),
                "std_ms": round(features[1], 2),
                "median_ms": round(features[2], 2),
            }
        }, ensure_ascii=False)

    def _get_model_info(self) -> str:
        """Вернуть статус и метрики модели.

        Returns:
            str: JSON со статусом модели.
        """
        if self._model is None:
            return json.dumps({"status": "not_trained", "message": "Модель не обучена"})

        return json.dumps({
            "status": "ready",
            "accuracy": self._accuracy,
            "users": self._trained_users,
            "total_sessions": self._train_samples,
            "features": ["mean_ms", "std_ms", "median_ms", "min_ms", "max_ms", "iqr_ms"]
        }, ensure_ascii=False)

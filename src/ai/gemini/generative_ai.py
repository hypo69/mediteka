## \file src/ai/gemini/generative_ai.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
.. module::  src.ai.gemini.generative_ai
   :platform: Windows, Unix
   :synopsis: Google generative AI integration
   https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai.md
"""
import re
import asyncio
import time
from io import IOBase
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field

from google import genai
from google.genai import types
import requests

from grpc import RpcError
from google.api_core.exceptions import (
    GatewayTimeout,
    ServiceUnavailable,
    ResourceExhausted,
    InvalidArgument,
)
from google.auth.exceptions import DefaultCredentialsError, RefreshError

import os
from dotenv import load_dotenv, set_key

import header
from header import __root__
from src.logger.logger import logger
from src.secrets.api_key_state import mark_exhausted, load_api_keys, get_status, update_last_run, next_available_in

_ENV_PATH = __root__ / '.env'

from src.utils.date_time import TimeoutCheck
from src.utils.jjson import j_loads
from src.utils.image import get_image_bytes

timeout_check = TimeoutCheck()

def normalize_text(text):
    # Декодируем все Unicode escape-последовательности
    #text = codecs.decode(text, 'unicode_escape')
    
    # Заменяем escape-последовательности HTML, если необходимо (например, <br>)
    text = re.sub(r'\\n', '\n', text)  # Заменяем \n на настоящий символ новой строки

    return text

def remove_html_blocks(text: str) -> str:
    """
    Удаляет блоки текста, которые начинаются с '```html' и заканчиваются на '```' или '```\n'.

    Args:
        text (str): Входной текст.

    Returns:
        str: Текст без блоков '```html'.
    """
    return re.sub(r'```html.*?```', '', text, flags=re.DOTALL)

_gemini_config = j_loads(Path(__file__).parent / 'config.json')
_DEFAULT_MODEL: str = _gemini_config.get('model', 'gemini-2.0-flash-exp') if isinstance(_gemini_config, dict) else 'gemini-2.0-flash-exp'
_AVAILABLE_MODELS: list = _gemini_config.get('model_choices', []) if isinstance(_gemini_config, dict) else []
_DEFAULT_SAVE_HISTORY: bool = _gemini_config.get('save_history_chat', False) if isinstance(_gemini_config, dict) else False


@dataclass
class GoogleGenerativeAI:
    """
    Класс для взаимодействия с моделями Google Generative AI.
    """

    api_key: str = field(default='')
    model_name: str = field(default_factory=lambda: _DEFAULT_MODEL)
    generation_config: Dict = field(default_factory=lambda: {"response_mime_type": "text/plain"})
    system_instruction: Optional[str] = None
    api_key_names: List[str] = field(default_factory=list)
    api_keys: List[str] = field(default_factory=list, init=False)
    api_key_owners: List[str] = field(default_factory=list, init=False)
    _key_names_active: List[str] = field(default_factory=list, init=False)
    chat_history: List[Dict] = field(default_factory=list, init=False)
    _client: Any = field(init=False)
    _chat: Any = field(init=False)
    _api_key_index: int = field(default=0, init=False)
    _all_keys_exhausted: bool = field(default=False, init=False)
    _unavailable_attempts: int = field(default=0, init=False)
    save_history_chat: bool = field(default_factory=lambda: _DEFAULT_SAVE_HISTORY)

    MODELS: List[str] = field(default_factory=lambda: _AVAILABLE_MODELS, init=False)

    def __post_init__(self):
        """Инициализация модели GoogleGenerativeAI с дополнительными настройками."""
        # Сброс счётчика неудачных 503 при новом запуске
        self._unavailable_attempts = 0
        self.api_keys, self._key_names_active, _ = load_api_keys(self.api_key_names or None)
        self.api_key_owners = self._key_names_active  # имя и есть владелец
        if not self.api_keys:
            print("[!] No available API keys.")
            self._all_keys_exhausted = True
            return
        get_status(self.api_key_names or None)
        self.api_key = self.api_keys[0]
        print(f"[API KEY] Using: {self._key_names_active[0]}")
        self._client = genai.Client(api_key=self.api_key)
        self._chat = self._start_chat()

    def _invalidate_api_key(self, key: str) -> None:
        """Логирует невалидный ключ и удаляет его из активного пула."""
        idx = self.api_keys.index(key) if key in self.api_keys else -1
        key_name = self._key_names_active[idx] if 0 <= idx < len(self._key_names_active) else '?'
        logger.warning(f"Invalid API key removed: {key_name}", None, False)
        self.api_keys = [k for k in self.api_keys if k != key]
        if idx >= 0:
            self._key_names_active = [n for i, n in enumerate(self._key_names_active) if i != idx]
            self.api_key_owners = [o for i, o in enumerate(self.api_key_owners) if i != idx]

    def _mark_key_exhausted(self, key: str) -> None:
        idx = self.api_keys.index(key) if key in self.api_keys else -1
        key_name = self._key_names_active[idx] if 0 <= idx < len(self._key_names_active) else key
        mark_exhausted(key_name)
        print(f"[!] Daily quota exhausted: {key_name}. Banned for 24h.")
        logger.warning(f"Daily quota exhausted. {key_name} banned 24h.", None, False)
        self.api_keys = [k for k in self.api_keys if k != key]
        if idx >= 0:
            self._key_names_active = [n for i, n in enumerate(self._key_names_active) if i != idx]

    def _switch_api_key(self) -> bool:
        """Переключается на первый доступный ключ в пуле.
        Если ключей нет — ждёт разблокировки ближайшего. Возвращает False только при критической ошибке.
        """
        if not self.api_keys:
            wait_sec = next_available_in(None)  # Поиск среди всех ключей файла, включая удалённые из пула
            if wait_sec > 0:
                h, rem = divmod(int(wait_sec), 3600)
                m = rem // 60
                print(f"[!] All API keys exhausted. Waiting {h}h {m}m for next key...")
                logger.warning(f"All keys exhausted. Sleeping {h}h {m}m", None, False)
                time.sleep(wait_sec + 5)
                # Перезагружаем ключи после ожидания
                self.api_keys, self._key_names_active, _ = load_api_keys(self.api_key_names or None)
                if not self.api_keys:
                    self._all_keys_exhausted = True
                    return False
                self._all_keys_exhausted = False
            else:
                self._all_keys_exhausted = True
                print("[!] All API keys exhausted and no recovery time available.")
                logger.warning("All API keys exhausted", None, False)
                return False
        self._api_key_index = 0
        self.api_key = self.api_keys[0]
        key_name = self._key_names_active[0] if self._key_names_active else '?'
        print(f"[API KEY] Switched to: {key_name}")
        self._client = genai.Client(api_key=self.api_key)
        self._chat = self._start_chat()
        logger.info(f"Switched to API key: {key_name}", None, False)
        return True

    def _build_content_config(self, instruction: str = "", tools: list = (), generation_config: dict = {}) -> types.GenerateContentConfig:
        cfg_kwargs = {}
        inst = instruction or self.system_instruction or ""
        if inst:
            format_rule = (
                "\n\nCRITICAL: You must format your response exactly as follows, with no extra text outside these blocks:\n"
                "[CHAT]\n<detailed styled markdown response in Russian for the user to read>\n"
                "[VOICE]\n<very concise, clear speech-friendly Russian text for the narrator, using only Russian letters, no markdown, no special symbols, write all numbers as words>"
            )
            inst += format_rule
            cfg_kwargs['system_instruction'] = inst
        if tools:
            cfg_kwargs['tools'] = tools
        
        gen_cfg = {}
        if isinstance(self.generation_config, dict):
            gen_cfg.update(self.generation_config)
        if generation_config:
            gen_cfg.update(generation_config)

        if gen_cfg:
            for k in ['temperature', 'top_p', 'top_k', 'response_mime_type']:
                val = gen_cfg.get(k)
                if val:
                    cfg_kwargs[k] = val
        return types.GenerateContentConfig(**cfg_kwargs)

    def _start_chat(self):
        """Запуск чата с начальной настройкой."""
        config = self._build_content_config()
        
        # Если save_history_chat=False, используем просто send_message без создания чата
        if not self.save_history_chat:
            return None
        
        return self._client.chats.create(model=self.model_name, config=config)

    def _switch_model(self) -> bool:
        """Переключается на следующую модель из списка. Возвращает False если модели закончились."""
        if not self.MODELS:
            return False
        try:
            idx = self.MODELS.index(self.model_name)
            next_idx = (idx + 1) % len(self.MODELS)
        except ValueError:
            next_idx = 0
        next_model = self.MODELS[next_idx]
        if next_model == self.model_name:
            return False
        logger.info(f"Switching model: {self.model_name} -> {next_model}", None, False)
        self.model_name = next_model
        # Перезагружаем все ключи — у новой модели могут быть другие квоты
        self.api_keys, self._key_names_active, _ = load_api_keys(self.api_key_names or None)
        if not self.api_keys:
            return False
        self._all_keys_exhausted = False
        self.api_key = self.api_keys[0]
        self._client = genai.Client(api_key=self.api_key)
        self._chat = self._start_chat()
        print(f"[MODEL] Switched to: {next_model}, key: {self._key_names_active[0]}")
        return True

    def _switch_model_down(self) -> bool:
        """Переключается на модель НЕ выше текущей (только вниз по списку мощности).
        Возвращает False если уже самая слабая модель."""
        if not self.MODELS:
            return False
        try:
            idx = self.MODELS.index(self.model_name)
        except ValueError:
            idx = 0
        # Выбираем следующую модель в списке (которая ниже по мощности)
        # Список отсортирован от мощных к лёгким, поэтому idx+1 — это менее мощная модель
        next_idx = idx + 1
        if next_idx >= len(self.MODELS):
            # Уже самая слабая модель
            return False
        next_model = self.MODELS[next_idx]
        logger.info(f"Switching model down: {self.model_name} -> {next_model}", None, False)
        self.model_name = next_model
        # Перезагружаем все ключи — у новой модели могут быть другие квоты
        self.api_keys, self._key_names_active, _ = load_api_keys(self.api_key_names or None)
        if not self.api_keys:
            return False
        self._all_keys_exhausted = False
        self.api_key = self.api_keys[0]
        self._client = genai.Client(api_key=self.api_key)
        self._chat = self._start_chat()
        print(f"[MODEL] Switched down to: {next_model}, key: {self._key_names_active[0]}")
        return True

    async def embed(self, text: str, model_name: str = "text-embedding-004") -> Optional[np.ndarray]:
        """Генерация эмбеддинга для текста."""
        try:
            response = self._client.models.embed_content(
                model=model_name,
                contents=text,
            )
            return np.array(response.embeddings[0].values)
        except Exception as ex:
            logger.error("Ошибка генерации эмбеддинга", ex, False)
            return None

    def clear_history(self):
        """Очищает историю чата в памяти."""
        self.chat_history = []

    def _restore_chat_from_history(self):
        """Восстанавливает сессию чата из chat_history в памяти."""
        self._chat = self._start_chat()
        for entry in self.chat_history:
            self._chat.history.append(
                types.Content(role=entry['role'], parts=[types.Part.from_text(text=p) for p in entry['parts']])
            )

    def _prepare_contents(self, q: str, history: Optional[List[Dict]] = None) -> List[types.Content]:
        """Подготавливает список объектов Content для stateless API-запроса."""
        contents = []
        if history:
            for entry in history:
                role = entry.get('role')
                if not role:
                    continue
                if role == 'assistant':
                    role = 'model'
                
                parts = entry.get('parts')
                if not parts:
                    content = entry.get('content')
                    if content:
                        parts = [types.Part.from_text(text=content)]
                else:
                    new_parts = []
                    for p in parts:
                        if isinstance(p, str):
                            new_parts.append(types.Part.from_text(text=p))
                        elif isinstance(p, dict) and 'text' in p:
                            new_parts.append(types.Part.from_text(text=p['text']))
                        else:
                            new_parts.append(p)
                    parts = new_parts
                
                if parts:
                    contents.append(types.Content(role=role, parts=parts))
        
        contents.append(types.Content(role='user', parts=[types.Part.from_text(text=q)]))
        return contents

    async def chat(self, q: str, history: Optional[List[Dict]] = None, flag: str = "save_chat", system_instruction: Optional[str] = None, attempts: int = 15, model_name: Optional[str] = None) -> Optional[str]:
        """
        Обрабатывает чат-запрос.

        Args:
            q (str): Вопрос пользователя.
            history (Optional[List[Dict]]): История чата из БД. Если передана — восстанавливает сессию.
            flag (str): "clear" или "start_new" — сбрасывает историю перед запросом.
            system_instruction (Optional[str]): Временная системная инструкция.
            attempts (int): Максимальное количество попыток.
            model_name (Optional[str]): Имя используемой модели.

        Returns:
            Optional[str]: Ответ модели.
        """
        if self._all_keys_exhausted:
            if not self._switch_api_key():
                print("[!] All API keys exhausted. Aborting.")
                return None
            self._all_keys_exhausted = False

        for attempt in range(attempts):
            response = None
            try:
                # Если save_history_chat=False, не используем историю чата
                instruction = system_instruction or self.system_instruction
                active_model = model_name or self.model_name
                if not self.save_history_chat:
                    # Используем одиночный запрос без сохранения истории
                    config = self._build_content_config(instruction or "")
                    response = self._client.models.generate_content(
                        model=active_model,
                        contents=q,
                        config=config,
                    )
                    if response and response.text:
                        response_text = normalize_text(response.text)
                        response_text = remove_html_blocks(response_text)
                        update_last_run(self._key_names_active[0] if self._key_names_active else '')
                        # Сброс счётчика неудачных 503 после успешного запроса
                        self._unavailable_attempts = 0
                        return response_text
                    # Пустой ответ — повторяем
                    logger.debug(f"No response from the model in chat. Attempt: {attempt}\nSleeping for {2 ** attempt}", None, False)
                    time.sleep(2**attempt)
                    continue
                
                # Старая логика с историей чата
                if history is not None:
                    self.chat_history = history
                    self._restore_chat_from_history()
                elif flag == "clear" or flag == "start_new":
                    self.chat_history = []
                    self._chat = self._start_chat()

                response = self._chat.send_message(q)
                if response and response.text:
                    response_text = normalize_text(response.text)
                    response_text = remove_html_blocks(response_text)
                    self.chat_history.append({"role": "user", "parts": [q]})
                    self.chat_history.append({"role": "model", "parts": [response_text]})
                    # Сброс счётчика неудачных 503 после успешного запроса
                    self._unavailable_attempts = 0
                    return response_text
                else:
                    logger.error("Empty response in chat", None, False)
                    time.sleep(2**attempt)
                    continue

            except Exception as ex:
                ex_str = str(ex)
                logger.error(f"Ошибка чата (attempt {attempt}):\n {response=}", ex, False)
                
                # Обработка ошибок как в методе ask()
                if '401' in ex_str or 'API_KEY_INVALID' in ex_str or 'PERMISSION_DENIED' in ex_str:
                    self._invalidate_api_key(self.api_key)
                    if not self._switch_api_key():
                        return None
                    continue
                
                if '503' in ex_str or 'UNAVAILABLE' in ex_str:
                    self._unavailable_attempts += 1
                    if self._unavailable_attempts < 6:
                        wait = 2 ** min(self._unavailable_attempts, 5)
                        logger.info(f"503 UNAVAILABLE (attempt {self._unavailable_attempts}). Waiting {wait}s...", None, False)
                        time.sleep(wait)
                        continue
                    else:
                        if not self._switch_model_down():
                            return None
                        self._unavailable_attempts = 0
                        continue
                
                if '429' in ex_str or 'RESOURCE_EXHAUSTED' in ex_str:
                    if 'PerDay' in ex_str or 'per_day' in ex_str.lower() or "quota_limit_value': '0'" in ex_str:
                        self._mark_key_exhausted(self.api_key)
                        if not self._switch_api_key():
                            if not self._switch_model():
                                return None
                        continue
                    m = re.search(r'retry\D*(\d+(?:\.\d+)?)s', ex_str, re.IGNORECASE)
                    base_wait = int(float(m.group(1))) + 2 if m else 5
                    wait = min(base_wait * (2 ** min(attempt, 3)), 60)
                    logger.info(f"Rate limit 429 (retry_after). Waiting {wait}s before retry (attempt {attempt})", None, False)
                    time.sleep(wait)
                    continue
                
                if attempt >= attempts - 1:
                    return None
                time.sleep(2 ** attempt)
                continue

        return None

    async def chat_stream(self, q: str, history: Optional[List[Dict]] = None, flag: str = "save_chat", system_instruction: Optional[str] = None, attempts: int = 15, model_name: Optional[str] = None, generation_config: dict = {}):
        """
        Асинхронный генератор ответов модели.
        """
        if self._all_keys_exhausted:
            if not self._switch_api_key():
                print("[!] All API keys exhausted. Aborting.")
                yield "Ошибка: Все API ключи исчерпаны."
                return
            self._all_keys_exhausted = False

        for attempt in range(attempts):
            try:
                instruction = system_instruction or self.system_instruction
                active_model = model_name or self.model_name
                
                if not self.save_history_chat:
                    config = self._build_content_config(instruction or "", generation_config=generation_config)
                    contents = self._prepare_contents(q, history)

                    # Run blocking Gemini streaming in thread pool to avoid blocking event loop
                    def _collect_stateless(_client=self._client, _model=active_model, _contents=contents, _config=config):
                        result = []
                        for _chunk in _client.models.generate_content_stream(
                            model=_model,
                            contents=_contents,
                            config=_config,
                        ):
                            if _chunk.text:
                                result.append(_chunk.text)
                        return result

                    chunks = await asyncio.to_thread(_collect_stateless)
                    if chunks:
                        for chunk_text in chunks:
                            yield chunk_text
                        update_last_run(self._key_names_active[0] if self._key_names_active else '')
                        self._unavailable_attempts = 0
                        return

                    await asyncio.sleep(2 ** attempt)
                    continue
                
                if history is not None:
                    self.chat_history = history
                    self._restore_chat_from_history()
                elif flag == "clear" or flag == "start_new":
                    self.chat_history = []
                    self._chat = self._start_chat()

                # Run blocking chat streaming in thread pool
                _chat_ref = self._chat
                def _collect_chat(_chat=_chat_ref, _q=q):
                    result = []
                    for _chunk in _chat.send_message_stream(_q):
                        if _chunk.text:
                            result.append(_chunk.text)
                    return result

                chunks = await asyncio.to_thread(_collect_chat)
                full_response_text = "".join(chunks)

                if full_response_text:
                    for chunk_text in chunks:
                        yield chunk_text
                    normalized = normalize_text(full_response_text)
                    normalized = remove_html_blocks(normalized)
                    self.chat_history.append({"role": "user", "parts": [q]})
                    self.chat_history.append({"role": "model", "parts": [normalized]})
                    self._unavailable_attempts = 0
                    return
                else:
                    logger.error("Empty response stream in chat", None, False)
                    await asyncio.sleep(2 ** attempt)
                    continue

            except Exception as ex:
                ex_str = str(ex)
                logger.error(f"Ошибка чата-стриминга (attempt {attempt}):", ex, False)
                
                if '401' in ex_str or 'API_KEY_INVALID' in ex_str or 'PERMISSION_DENIED' in ex_str:
                    self._invalidate_api_key(self.api_key)
                    if not self._switch_api_key():
                        yield "Ошибка авторизации (API_KEY_INVALID)."
                        return
                    continue
                
                if '503' in ex_str or 'UNAVAILABLE' in ex_str:
                    self._unavailable_attempts += 1
                    if self._unavailable_attempts < 6:
                        wait = 2 ** min(self._unavailable_attempts, 5)
                        logger.info(f"503 UNAVAILABLE (attempt {self._unavailable_attempts}). Waiting {wait}s...", None, False)
                        await asyncio.sleep(wait)
                        continue
                    else:
                        if not self._switch_model_down():
                            yield "Ошибка: Модель недоступна (503)."
                            return
                        self._unavailable_attempts = 0
                        continue

                if '429' in ex_str or 'RESOURCE_EXHAUSTED' in ex_str:
                    if 'PerDay' in ex_str or 'per_day' in ex_str.lower() or "quota_limit_value': '0'" in ex_str:
                        self._mark_key_exhausted(self.api_key)
                        if not self._switch_api_key():
                            if not self._switch_model():
                                yield "Ошибка: Лимиты исчерпаны (429)."
                                return
                        continue
                    m = re.search(r'retry\D*(\d+(?:\.\d+)?)s', ex_str, re.IGNORECASE)
                    base_wait = int(float(m.group(1))) + 2 if m else 5
                    wait = min(base_wait * (2 ** min(attempt, 3)), 60)
                    logger.info(f"Rate limit 429 (retry_after). Waiting {wait}s before retry (attempt {attempt})", None, False)
                    await asyncio.sleep(wait)
                    continue

                if attempt >= attempts - 1:
                    yield f"Ошибка: {ex_str}"
                    return
                await asyncio.sleep(2 ** attempt)
                continue

    async def ask(self, q: str, attempts: int = 15, generation_config: dict = {}) -> Optional[str]:
        """
        Метод отправляет текстовый запрос модели и возвращает ответ.
        """
        if self._all_keys_exhausted:
            if not self._switch_api_key():
                print("[!] All API keys exhausted. Aborting.")
                return None
            self._all_keys_exhausted = False
        for attempt in range(attempts):
            try:
                # При save_history_chat=False не используем _chat, отправляем напрямую
                config = self._build_content_config(generation_config=generation_config)
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=q,
                    config=config,
                )
               
                if not response.text:
                    logger.debug(
                        f"No response from the model. Attempt: {attempt}\nSleeping for {2 ** attempt}",
                        None,
                        False
                    )
                    time.sleep(2**attempt)
                    continue  # Повторить попытку
                response_text = normalize_text(response.text)
                response_text = remove_html_blocks(response.text)
                update_last_run(self._key_names_active[0] if self._key_names_active else '')
                # Сброс счётчика неудачных 503 после успешного запроса
                self._unavailable_attempts = 0
                return response_text

            except requests.exceptions.RequestException as ex:
                max_attempts = 5
                if attempt > max_attempts:
                    break
                logger.debug(
                    f"Network error. Attempt: {attempt}\nSleeping for 20 min",
                    ex,
                    False,
                )
                time.sleep(1200)
                continue  # Повторить попытку
            except (GatewayTimeout, ServiceUnavailable) as ex:
                # Модель недоступна — переключаемся на следующую из model_choices в config.json.
                # Если все модели исчерпаны (_switch_model вернул False) — ждём и повторяем.
                logger.error("Service unavailable:", ex, False)
                self._unavailable_attempts += 1
                if self._unavailable_attempts < 6:
                    # До 6 попыток — просто перезапускаем с той же моделью
                    wait = 2 ** min(self._unavailable_attempts, 5)
                    logger.info(f"503 UNAVAILABLE (attempt {self._unavailable_attempts}). Waiting {wait}s...", None, False)
                    time.sleep(wait)
                    continue
                else:
                    # После 6 попыток — переключаемся на модель НЕ выше текущей
                    if not self._switch_model_down():
                        time.sleep(2**attempt + 10)
                    self._unavailable_attempts = 0
                    continue
            except ResourceExhausted as ex:
                ex_str = str(ex)
                if 'PerDay' in ex_str or 'per_day' in ex_str.lower() or 'quota_limit_value.*0' in ex_str or "quota_limit_value': '0'" in ex_str:
                    self._mark_key_exhausted(self.api_key)
                    if not self._switch_api_key():
                        if not self._switch_model():
                            return
                    continue
                # Короткий таймаут (retry_after) — не является исчерпанием квоты
                m = re.search(r'retry\D*(\d+(?:\.\d+)?)s', ex_str, re.IGNORECASE)
                base_wait = int(float(m.group(1))) + 2 if m else 5
                # Ограничиваем максимальное время ожидания для retry_after
                wait = min(base_wait * (2 ** min(attempt, 3)), 60)
                logger.info(f"ResourceExhausted 429 (retry_after). Waiting {wait}s before retry (attempt {attempt})", None, False)
                time.sleep(wait)
                continue
            except (DefaultCredentialsError, RefreshError) as ex:
                logger.error("Authentication error:", ex, False)
                self._invalidate_api_key(self.api_key)
                if not self._switch_api_key():
                    return
                continue
            except (ValueError, TypeError) as ex:
                max_attempts = 3
                if attempt > max_attempts:
                    break
                timeout = 5
                logger.error(
                    f"Invalid input: Attempt: {attempt}\nSleeping for {timeout/60} min",
                    ex,
                    None,
                )
                time.sleep(timeout)
                continue
            except (InvalidArgument, RpcError) as ex:
                logger.error("API error:", ex, False)
                return
            except Exception as ex:
                ex_str = str(ex)
                logger.error(f"Unexpected error: {ex_str}", ex, False)
                if '401' in ex_str or 'API_KEY_INVALID' in ex_str or 'PERMISSION_DENIED' in ex_str:
                    self._invalidate_api_key(self.api_key)
                    if not self._switch_api_key():
                        return
                    continue
                if '503' in ex_str or 'UNAVAILABLE' in ex_str:
                    self._unavailable_attempts += 1
                    if self._unavailable_attempts < 6:
                        # До 6 попыток — просто перезапускаем с той же моделью
                        wait = 2 ** min(self._unavailable_attempts, 5)
                        logger.info(f"503 UNAVAILABLE (attempt {self._unavailable_attempts}). Waiting {wait}s...", None, False)
                        time.sleep(wait)
                        continue
                    else:
                        # После 6 попыток — переключаемся на модель НЕ выше текущей
                        if not self._switch_model_down():
                            return
                        self._unavailable_attempts = 0
                        continue
                if '429' in ex_str or 'RESOURCE_EXHAUSTED' in ex_str:
                    # Проверяем, это дневная квота или короткий retry_after
                    if 'PerDay' in ex_str or 'per_day' in ex_str.lower() or "quota_limit_value': '0'" in ex_str:
                        self._mark_key_exhausted(self.api_key)
                        if not self._switch_api_key():
                            if not self._switch_model():
                                return
                        continue
                    # Короткий таймаут — retry_after
                    m = re.search(r'retry\D*(\d+(?:\.\d+)?)s', ex_str, re.IGNORECASE)
                    base_wait = int(float(m.group(1))) + 2 if m else 5
                    wait = min(base_wait * (2 ** min(attempt, 3)), 60)
                    logger.info(f"Rate limit 429 (retry_after). Waiting {wait}s before retry (attempt {attempt})", None, False)
                    time.sleep(wait)
                    continue
                return

        return


    async def ask_with_tools(self, q: str, tools: list, tool_dispatcher, system_instruction: Optional[str] = None, model_name: Optional[str] = None) -> str:
        """Отправка запроса с поддержкой function calling (agentic loop).

        Модель сама решает когда вызвать инструмент. Цикл продолжается
        пока модель возвращает function calls; финальный текстовый ответ
        возвращается вызывающему коду.

        Args:
            q (str): Вопрос пользователя.
            tools (list): Список types.Tool для передачи модели.
            tool_dispatcher: Callable(name, args) -> str — диспетчер вызовов.
            system_instruction (Optional[str]): Временная системная инструкция.
            model_name (Optional[str]): Имя используемой модели.

        Returns:
            str: Финальный текстовый ответ модели.

        Examples:
            >>> from plugins.media_organizer.media_tools import MEDIA_TOOLS, dispatch_tool_call
            >>> answer = await ai.ask_with_tools('Карточка Титаника', [MEDIA_TOOLS], dispatch_tool_call)
        """
        contents = [types.Content(role='user', parts=[types.Part.from_text(text=q)])]
        instruction = system_instruction or self.system_instruction
        active_model = model_name or self.model_name
        config = self._build_content_config(instruction or "", tools)
        for _ in range(10):  # Максимум 10 итераций agentic loop
            response = self._client.models.generate_content(
                model=active_model,
                contents=contents,
                config=config,
            )
            candidate = response.candidates[0] if response.candidates else None
            if not candidate:
                break

            # Сбор всех частей ответа
            tool_calls = [p for p in candidate.content.parts if p.function_call]
            text_parts = [p.text for p in candidate.content.parts if p.text]

            if not tool_calls:
                # Финальный текстовый ответ — выходим из цикла
                return '\n'.join(text_parts)

            # Добавляем ответ модели в историю
            contents.append(candidate.content)

            # Выполняем все function calls и добавляем результаты
            tool_results = []
            for part in tool_calls:
                fc = part.function_call
                result = tool_dispatcher(fc.name, dict(fc.args))
                tool_results.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={'result': result},
                    )
                )
            contents.append(types.Content(role='tool', parts=tool_results))

        return ''

    async def ask_with_tools_stream(self, q: str, tools: list, tool_dispatcher, system_instruction: Optional[str] = None, model_name: Optional[str] = None, history: Optional[List[Dict]] = None):
        """Отправка запроса с поддержкой function calling и стримингом.

        Yields:
            dict: События вида {"text": "chunk"} или {"status": "message"}
        """
        contents = self._prepare_contents(q, history)
        instruction = system_instruction or self.system_instruction
        active_model = model_name or self.model_name
        config = self._build_content_config(instruction or "", tools)
        for i in range(10):
            # Нам не нужен стриминг, если модель решает вызвать функцию.
            # Стриминг нужен только для финального ответа.
            response = self._client.models.generate_content(
                model=active_model,
                contents=contents,
                config=config,
            )
            
            candidate = response.candidates[0] if response.candidates else None
            if not candidate:
                break

            tool_calls = [p for p in candidate.content.parts if p.function_call]
            text_parts = [p.text for p in candidate.content.parts if p.text]

            # Если вызовов функций больше нет, значит это финальный ответ.
            if not tool_calls:
                # Стримим финальный ответ
                response_stream = self._client.models.generate_content_stream(
                    model=active_model,
                    contents=contents,
                    config=config,
                )
                for chunk in response_stream:
                    if chunk.text:
                        yield {"text": chunk.text}
                return

            # Добавляем ответ модели с вызовом функций в контекст
            contents.append(candidate.content)

            tool_results = []
            for part in tool_calls:
                fc = part.function_call
                import json
                yield {"status": f"Вызов функции {fc.name}({json.dumps(dict(fc.args), ensure_ascii=False)})"}
                result = tool_dispatcher(fc.name, dict(fc.args))
                tool_results.append(
                    types.Part.from_function_response(
                        name=fc.name,
                        response={'result': result},
                    )
                )
            contents.append(types.Content(role='tool', parts=tool_results))



    async def describe_image(
        self, image: Path | bytes, mime_type: Optional[str] = 'image/jpeg', prompt: Optional[str] = '', attempts: int = 10
    ) -> Optional[str]:
        """
        Отправляет изображение в Gemini Pro Vision и возвращает его текстовое описание.

        Args:
            image: Путь к файлу изображения или байты изображения
            mime_type: MIME тип изображения
            prompt: Промпт для описания
            attempts: Максимальное количество попыток

        Returns:
            str: Текстовое описание изображения.
            None: Если произошла ошибка.
        """
        ex_str = ""
        for attempt in range(attempts):
            try:
                if isinstance(image, Path):
                    image = get_image_bytes(image)

                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_bytes(data=image, mime_type=mime_type),
                        types.Part.from_text(text=prompt),
                    ],
                )
                if response.text:
                    return response.text
                else:
                    print("Модель вернула пустой ответ.")
                    time.sleep(2**attempt)
                    continue

            except Exception as ex:
                ex_str = str(ex)
                logger.error(f"Ошибка описания изображения (attempt {attempt}):", ex, False)
                
                if '401' in ex_str or 'API_KEY_INVALID' in ex_str or 'PERMISSION_DENIED' in ex_str:
                    self._invalidate_api_key(self.api_key)
                    if not self._switch_api_key():
                        return None
                    continue
                
                if '503' in ex_str or 'UNAVAILABLE' in ex_str:
                    self._unavailable_attempts += 1
                    if self._unavailable_attempts < 6:
                        wait = 2 ** min(self._unavailable_attempts, 5)
                        logger.info(f"503 UNAVAILABLE (attempt {self._unavailable_attempts}). Waiting {wait}s...", None, False)
                        time.sleep(wait)
                        continue
                    else:
                        if not self._switch_model_down():
                            return None
                        self._unavailable_attempts = 0
                        continue
                
                if '429' in ex_str or 'RESOURCE_EXHAUSTED' in ex_str:
                    if 'PerDay' in ex_str or 'per_day' in ex_str.lower() or "quota_limit_value': '0'" in ex_str:
                        self._mark_key_exhausted(self.api_key)
                        if not self._switch_api_key():
                            if not self._switch_model():
                                return None
                        continue
                    m = re.search(r'retry\D*(\d+(?:\.\d+)?)s', ex_str, re.IGNORECASE)
                    base_wait = int(float(m.group(1))) + 2 if m else 5
                    wait = min(base_wait * (2 ** min(attempt, 3)), 60)
                    logger.info(f"Rate limit 429 (retry_after). Waiting {wait}s before retry (attempt {attempt})", None, False)
                    time.sleep(wait)
                    continue
                
                if attempt >= attempts - 1:
                    return None
                time.sleep(2 ** attempt)
                continue
        
        return None

    async def upload_file(
        self, file: str | Path | IOBase, file_name: Optional[str] = None, attempts: int = 10
    ) -> bool:
        """
        https://github.com/google-gemini/generative-ai-python/blob/main/docs/api/google/generativeai/upload_file.md
        response (file_types.File)
        """

        response = None
        ex_str = ""
        for attempt in range(attempts):
            try:
                response = self._client.files.upload(path=file, config=types.UploadFileConfig(display_name=file_name))
                logger.debug(f"Файл {file_name} записан", None, False)
                return response
            except Exception as ex:
                ex_str = str(ex)
                logger.error(f"Ошибка записи файла {file_name=} (attempt {attempt}):", ex, False)
                
                if '401' in ex_str or 'API_KEY_INVALID' in ex_str or 'PERMISSION_DENIED' in ex_str:
                    self._invalidate_api_key(self.api_key)
                    if not self._switch_api_key():
                        return False
                    continue
                
                if '503' in ex_str or 'UNAVAILABLE' in ex_str:
                    self._unavailable_attempts += 1
                    if self._unavailable_attempts < 6:
                        wait = 2 ** min(self._unavailable_attempts, 5)
                        logger.info(f"503 UNAVAILABLE (attempt {self._unavailable_attempts}). Waiting {wait}s...", None, False)
                        time.sleep(wait)
                        continue
                    else:
                        if not self._switch_model_down():
                            return False
                        self._unavailable_attempts = 0
                        continue
                
                if '429' in ex_str or 'RESOURCE_EXHAUSTED' in ex_str:
                    if 'PerDay' in ex_str or 'per_day' in ex_str.lower() or "quota_limit_value': '0'" in ex_str:
                        self._mark_key_exhausted(self.api_key)
                        if not self._switch_api_key():
                            if not self._switch_model():
                                return False
                        continue
                    m = re.search(r'retry\D*(\d+(?:\.\d+)?)s', ex_str, re.IGNORECASE)
                    base_wait = int(float(m.group(1))) + 2 if m else 5
                    wait = min(base_wait * (2 ** min(attempt, 3)), 60)
                    logger.info(f"Rate limit 429 (retry_after). Waiting {wait}s before retry (attempt {attempt})", None, False)
                    time.sleep(wait)
                    continue
                
                if attempt >= attempts - 1:
                    return False
                time.sleep(2 ** attempt)
                continue
        
        logger.error(f" upload_file failed after {attempts} attempts: {ex_str}", None, False)
        return False


async def main():
    from dotenv import load_dotenv
    import os
    load_dotenv(__root__ / '.env')
    api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
    system_instruction = "Ты - полезный ассистент. Отвечай на все вопросы кратко"
    ai = GoogleGenerativeAI(api_key_names=api_key_names, system_instruction=system_instruction)

    # Пример вызова describe_image с промптом
    image_path = Path(r"test.jpg")  # Замените на путь к вашему изображению

    if not image_path.is_file():
        print(
            f"Файл {image_path} не существует. Поместите в корневую папку с программой файл с названием test.jpg"
        )
    else:
        prompt = """Проанализируй это изображение. Выдай ответ в формате JSON,
        где ключом будет имя объекта, а значением его описание.
         Если есть люди, опиши их действия."""

        description = await ai.describe_image(image_path, prompt=prompt)
        if description:
            print("Описание изображения (с JSON форматом):")
            print(description)
            try:
                parsed_description = j_loads(description)

            except Exception as ex:
                print("Не удалось распарсить JSON. Получен текст:")
                print(description)

        else:
            print("Не удалось получить описание изображения.")

        # Пример без JSON вывода
        prompt = "Проанализируй это изображение. Перечисли все объекты, которые ты можешь распознать."
        description = await ai.describe_image(image_path, prompt=prompt)
        if description:
            print("Описание изображения (без JSON формата):")
            print(description)

    file_path = Path('test.txt')
    with open(file_path, "w") as f:
        f.write("Hello, Gemini!")

    file_upload = await ai.upload_file(file_path, 'test_file.txt')
    print(file_upload)

    # Пример чата
    while True:
        user_message = input("You: ")
        if user_message.lower() == 'exit':
            break
        ai_message = await ai.chat(user_message)
        if ai_message:
            print(f"Gemini: {ai_message}")
        else:
            print("Gemini: Ошибка получения ответа")


if __name__ == "__main__":
    asyncio.run(main())
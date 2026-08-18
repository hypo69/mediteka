# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI-роутер чата
# =============================================================================
# Описание:
#   Обработка POST-запросов к /api/chat.
#   Последовательный опрос плагинов, извлечение контекста из пользовательского RAG,
#   прямой вызов AI-модели и автоматическая индексация диалога в User RAG.
#
# File: router_chat.py
# Project: mediteka
# Package: src.fastapi
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from __future__ import annotations

import os
import time
import asyncio
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.logger import logger
from src.config import ai_cfg, tts_cfg
from src.ai.gemini.user_query_rag import index_user_query, search_user_context

router = APIRouter(prefix='/api/chat', tags=['chat'])


# Короткие слова-продолжения диалога, которые сами по себе не содержат медиа-ключевых слов
_CONTEXT_CONTINUATION_WORDS = {
    'да', 'нет', 'yes', 'no', 'ок', 'ok', 'хочу', 'конечно',
    'давай', 'проверь', 'найди', 'покажи', 'ладно', 'угу', 'yep', 'sure',
    'want', 'check', 'find', 'show', 'okay',
}


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    generation_config: dict = {}


class SaveRagRequest(BaseModel):
    query: str
    chat_text: str
    voice_text: str


class TestModelRequest(BaseModel):
    model: str = ""
    provider: str = ""
    message: str = "Привет! Назови свою модель и провайдера, и подтверди готовность к работе."
    system_instruction: str = ""


def get_chat_model(selected_model_name: str, system_instruction: str = ""):
    """Dynamically construct/retrieve the appropriate AI model instance."""
    is_gemini_cli = selected_model_name.startswith('gemini_cli:') or selected_model_name.startswith('gemini-cli-')
    is_foundry = selected_model_name.startswith('foundry:')
    is_ollama = selected_model_name.startswith('ollama:')
    is_agy = selected_model_name.startswith('agy-') or 'agy' in selected_model_name.lower()
    is_gemini = not is_gemini_cli and (selected_model_name.startswith('gemini-') or 'gemini' in selected_model_name.lower())

    if is_gemini_cli:
        from src.ai.gemini_cli_chat import GeminiCliChatBase
        return GeminiCliChatBase(
            model_id=selected_model_name,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    elif is_foundry:
        # Явный префикс foundry: для выбора Foundry модели
        model_id = selected_model_name[len('foundry:'):]
        from src.ai.foundry_chat import FoundryChatBase
        return FoundryChatBase(
            model_id=model_id,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    elif is_ollama:
        model_id = selected_model_name[len('ollama:'):]
        from src.ai.ollama_chat import OllamaChatBase
        ollama_url = ai_cfg.ollama_base_url if ai_cfg else 'http://localhost:11434'
        return OllamaChatBase(
            model_id=model_id,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
            api_url=ollama_url
        )
    elif is_agy:
        from src.ai.agy_chat import AgyChatBase
        return AgyChatBase(
            model_id=selected_model_name,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    elif is_gemini:
        from src.ai.gemini.generative_ai import GoogleGenerativeAI
        _api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
        return GoogleGenerativeAI(
            model_name=selected_model_name,
            api_key_names=_api_key_names,
            system_instruction=system_instruction,
            sleep_on_exhausted=False,
        )
    else:
        # По умолчанию - Foundry для неизвестных моделей (обратная совместимость)
        from src.ai.foundry_chat import FoundryChatBase
        return FoundryChatBase(
            model_id=selected_model_name,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )


async def _extract_user_auth(fastapi_req: Request) -> tuple[str, str, str, dict]:
    """Извлекает идентификатор пользователя, системную инструкцию, модель и настройки из JWT/IP."""
    user_identifier = ""
    system_instruction = ""
    selected_model = ""
    settings = {}

    token = fastapi_req.cookies.get('auth_token')
    if token:
        from src.fastapi.router_auth import verify_jwt_token
        user_data = verify_jwt_token(token)
        if user_data:
            from src.user_manager import user_manager
            db_user = await asyncio.to_thread(user_manager.get_user_by_email, user_data.email)
            if db_user:
                user_identifier = str(db_user['id'])
                settings = await asyncio.to_thread(user_manager.get_user_settings, db_user['id']) or {}
                if settings.get('system_instruction'):
                    system_instruction = settings['system_instruction']
                if settings.get('model'):
                    selected_model = settings['model']

    if not user_identifier:
        client_ip = fastapi_req.client.host if fastapi_req.client else 'unknown'
        user_identifier = f"anon_{client_ip}"

    return user_identifier, system_instruction, selected_model, settings


def _get_voice_gender_rule(settings: dict) -> str:
    """Определяет гендерное правило для ответов ассистента на основе настроек голоса TTS."""
    default_voice = getattr(tts_cfg, "default_voice", "ru-RU-DmitryNeural") if tts_cfg else "ru-RU-DmitryNeural"
    tts_voice = settings.get('tts_voice', '') or default_voice
    voice_lower = tts_voice.lower()
    is_male_voice = any(name in voice_lower for name in ("dmitry", "yaraslaus", "male", "bayan", "aidar", "eugene", "georgy"))
    is_female_voice = any(name in voice_lower for name in ("svetlana", "elena", "female", "kseniya", "tanya", "aliona", "dariya"))
    if is_male_voice:
        return "ВАЖНОЕ ПРАВИЛО: Отвечай от мужского лица (например: 'Я нашел', 'Я подобрал')."
    if is_female_voice:
        return "ВАЖНОЕ ПРАВИЛО: Отвечай от женского лица (например: 'Я нашла', 'Я подобрала')."
    return ""


def _clean_chat_history(history: list[dict]) -> list[dict]:
    """Очищает историю сообщений перед передачей в модель."""
    if not history:
        return []
    _ERROR_PATTERNS = (
        '❌', 'Ошибка', 'Error', 'TypeError', 'AttributeError', 'Traceback',
        '[Ошибка]', 'Не удалось найти', 'В локальной базе ничего не найдено',
        'DEBUG MODE', 'DEBUG:', '[DEBUG'
    )
    _STATUS_PREFIXES = (
        '🔍', '🌐', '🤖', '🛠️', '🎡', '📡', 'Вызов плагина', 'Генерация', 'Проверка',
        'DEBUG MODE:', 'DEBUG:'
    )

    def _is_clean(entry: dict) -> bool:
        parts = entry.get('parts', [])
        text = ''
        if isinstance(parts, list) and len(parts) > 0:
            p = parts[0]
            text = p if isinstance(p, str) else p.get('text', '') if isinstance(p, dict) else ''
        elif isinstance(parts, str):
            text = parts
        text = (text or '').strip()
        if not text:
            return False
        if any(pfx in text for pfx in _ERROR_PATTERNS):
            return False
        if any(text.startswith(pfx) for pfx in _STATUS_PREFIXES):
            return False
        if text.startswith('{') and ('"title"' in text or '"error"' in text or '"genres"' in text):
            return False
        if 'Ответ модели: {' in text and '"title"' in text:
            return False
        return True

    def _compact_turn(entry: dict) -> dict:
        parts = entry.get('parts', [])
        text = ''
        if isinstance(parts, list) and len(parts) > 0:
            p = parts[0]
            text = p if isinstance(p, str) else p.get('text', '') if isinstance(p, dict) else ''
        elif isinstance(parts, str):
            text = parts

        if entry.get('role') in ('model', 'assistant') and len(text) > 200:
            import re
            compact = re.sub(r'<film>(.*?)</film>', r'«\1»', text, flags=re.IGNORECASE)
            compact = re.sub(r'#+\s*', '', compact)
            compact = re.sub(r'[*_`]+', '', compact)
            compact = re.sub(r'\s+', ' ', compact).strip()
            if len(compact) > 200:
                compact = compact[:197].rsplit(' ', 1)[0] + '...'
            return {'role': entry['role'], 'parts': [compact]}
        return entry

    raw_clean = [e for e in history if _is_clean(e)]
    cleaned_entries: list[dict] = []
    i = 0
    while i < len(raw_clean):
        entry = raw_clean[i]
        if entry.get('role') == 'user':
            if i + 1 < len(raw_clean) and raw_clean[i + 1].get('role') in ('model', 'assistant'):
                cleaned_entries.append(_compact_turn(entry))
                cleaned_entries.append(_compact_turn(raw_clean[i + 1]))
                i += 2
                continue
        i += 1

    return cleaned_entries[-10:]


def _build_debug_prompt(request: ChatRequest, user_context_str: str, voice_gender_rule: str) -> str:
    """Формирует текстовый дамп полного промпта для отладочного режима."""
    full_prompt_parts = []
    dynamic_parts = []
    if voice_gender_rule:
        dynamic_parts.append(voice_gender_rule)
    if user_context_str:
        dynamic_parts.append(user_context_str)
    if dynamic_parts:
        full_prompt_parts.append("── DYNAMIC CONTEXT ──\n" + "\n\n".join(dynamic_parts))

    clean_history = _clean_chat_history(request.history)
    if clean_history:
        full_prompt_parts.append("── CHAT HISTORY (последние 5) ──\n" + "\n---\n".join([
            f"{entry.get('role', 'unknown').upper()}:\n{entry.get('parts', [''])[0] if isinstance(entry.get('parts'), list) else entry.get('parts', '')}"
            for entry in clean_history[-5:]
        ]))

    full_prompt_parts.append(f"── USER MESSAGE ──\n{request.message}")
    return "\n\n".join(full_prompt_parts)


async def _try_auto_play_film(full_response_text: str, room_id: str) -> str | None:
    """Проверяет наличие тега <film> и отправляет команду на автозапуск в плеер."""
    import re as _re
    film_tags = _re.findall(r'<film>(.*?)</film>', full_response_text, _re.IGNORECASE)
    if not film_tags or not room_id:
        return None

    film_title = film_tags[0].strip()
    try:
        from plugins.media_organizer.core.database import MediaDatabase
        from plugins.media_organizer.core import MEDIA_DB
        from src.fastapi.router_control import manager
        _db_inst = MediaDatabase(MEDIA_DB)
        _records = await asyncio.to_thread(_db_inst.export_all)
        film_path = None
        _tl = film_title.lower()
        for rec in _records:
            r_t = rec.get('title', '').lower()
            r_ru = (rec.get('title_ru') or '').lower()
            r_orig = (rec.get('title_orig') or '').lower()
            if (r_t == _tl or r_ru == _tl or r_orig == _tl
                    or r_t.startswith(_tl) or (r_ru and r_ru.startswith(_tl))
                    or _tl in r_t or _tl in r_ru):
                if rec.get('path'):
                    film_path = rec['path']
                    break
        if film_path:
            asyncio.ensure_future(manager.broadcast_to_role(room_id, 'player', {
                'action': 'play_file_by_path',
                'path': film_path,
            }))
            return film_title
    except Exception as _fe:
        logger.error(f'[router_chat] Ошибка авто-запуска: {_fe}')
    return None


def init_router(chat_model, narrator_model, plugins: dict) -> APIRouter:
    """Инициализация роутера чата с привязкой моделей (chat и narrator) и плагинов."""
    if hasattr(narrator_model, 'gemini_model') and narrator_model.gemini_model:
        narrator_model.gemini_model.save_history_chat = False

    @router.get('/models')
    async def get_models(refresh: bool = False) -> dict:
        """Получение списка доступных моделей, сгруппированных по провайдеру."""
        from src.ai.model_manager import get_available_models

        gemini_models = get_available_models('gemini', force_refresh=refresh)
        
        foundry_raw = get_available_models('foundry', force_refresh=refresh)
        foundry_models = [f"foundry:{m}" if not m.startswith('foundry:') else m for m in foundry_raw]

        ollama_raw = get_available_models('ollama', force_refresh=refresh)
        ollama_models = [f"ollama:{m}" if not m.startswith('ollama:') else m for m in ollama_raw]

        agy_models = get_available_models('agy', force_refresh=refresh)

        gemini_cli_raw = get_available_models('gemini_cli', force_refresh=refresh)
        gemini_cli_models = [f"gemini_cli:{m}" if not m.startswith('gemini_cli:') else m for m in gemini_cli_raw]

        logger.info(f"Returning available gemini models (refresh={refresh}): {gemini_models}")
        logger.info(f"Returning available foundry models: {foundry_models}")
        logger.info(f"Returning available ollama models: {ollama_models}")
        logger.info(f"Returning available agy models: {agy_models}")
        logger.info(f"Returning available gemini_cli models: {gemini_cli_models}")
        
        return {
            'models': {
                'gemini': gemini_models,
                'foundry': foundry_models,
                'ollama': ollama_models,
                'agy': agy_models,
                'gemini_cli': gemini_cli_models
            }
        }

    @router.post('/test-model')
    async def test_model(req: TestModelRequest) -> dict:
        """Проверочный запрос к указанной AI-модели для валидации связи (Запрос -> Ответ).

        Args:
            req (TestModelRequest): Параметры проверочного запроса, включая имя модели,
                                    провайдера и тестовое сообщение.

        Returns:
            dict: Результат выполнения запроса со статусом, ответом модели и временем выполнения.

        Examples:
            >>> req = TestModelRequest(model="gemini-3.7-flash", message="Ping")
            >>> res = await test_model(req)
            >>> res['status'] == 'success'
            True
        """
        start_time = time.perf_counter()
        target_model = req.model.strip()
        provider = req.provider.strip().lower()

        # Автоматическое добавление префикса провайдера при необходимости
        if provider == 'foundry' and target_model and not target_model.startswith('foundry:'):
            target_model = f"foundry:{target_model}"
        elif provider == 'ollama' and target_model and not target_model.startswith('ollama:'):
            target_model = f"ollama:{target_model}"
        elif provider == 'agy' and target_model and not target_model.startswith('agy-'):
            target_model = f"agy-{target_model}"
        elif provider in ('gemini_cli', 'gemini-cli') and target_model and not target_model.startswith('gemini_cli:'):
            target_model = f"gemini_cli:{target_model}"

        if not target_model:
            return {
                'status': 'error',
                'message': 'Имя модели не указано',
                'model': '',
                'provider': provider,
                'duration_ms': 0.0
            }

        test_msg = req.message.strip()
        if not test_msg:
            test_msg = "Привет! Назови свою модель и провайдера, и подтверди готовность к работе."

        try:
            model_instance = get_chat_model(target_model, system_instruction=req.system_instruction)
            response_text = ""

            if hasattr(model_instance, 'ask'):
                response_text = await model_instance.ask(test_msg)
            elif hasattr(model_instance, 'chat'):
                response_text = await model_instance.chat(test_msg)
            elif hasattr(model_instance, 'chat_stream'):
                chunks = []
                async for chunk in model_instance.chat_stream(test_msg):
                    if chunk:
                        clean_chunk = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                        if clean_chunk:
                            chunks.append(clean_chunk)
                response_text = "".join(chunks)
            else:
                raise RuntimeError(f"Модель {target_model} не поддерживает методы генерации текста")

            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
            return {
                'status': 'success',
                'response': response_text,
                'model': target_model,
                'provider': provider,
                'duration_ms': duration_ms
            }
        except Exception as exc:
            logger.error(f"[ChatRouter] Ошибка проверочного запроса к модели {target_model}: {exc}", exc_info=True)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 1)
            return {
                'status': 'error',
                'message': str(exc),
                'model': target_model,
                'provider': provider,
                'duration_ms': duration_ms
            }

    @router.post('/save-rag')
    async def save_to_rag(request: SaveRagRequest, fastapi_req: Request):
        """Ручное сохранение одобренного ответа: только в JSON-хранилище (в архив)."""
        try:
            token = fastapi_req.cookies.get('auth_token')
            user_identifier = ""
            if token:
                from src.fastapi.router_auth import verify_jwt_token
                user_data = verify_jwt_token(token)
                if user_data:
                    from src.user_manager import user_manager
                    db_user = await asyncio.to_thread(user_manager.get_user_by_email, user_data.email)
                    if db_user:
                        user_identifier = db_user['id']

            if not user_identifier:
                client_ip = fastapi_req.client.host if fastapi_req.client else 'unknown'
                user_identifier = f"anon_{client_ip}"

            api_key = getattr(chat_model, 'api_key', '') or ''
            if not api_key:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()

            combined_response = f"Текст для чата:\n{request.chat_text}\n\nТекст для диктора:\n{request.voice_text}"

            from src.ai.gemini.chat_response_store import save_approved_response
            save_success = await asyncio.to_thread(
                save_approved_response,
                user_identifier, request.query, request.chat_text, request.voice_text
            )

            if save_success:
                return {"status": "success", "message": "Успешно сохранено для последующей компиляции RAG"}
            else:
                raise HTTPException(status_code=500, detail="Ошибка сохранения ответа")
        except Exception as e:
            logger.error("Ошибка при ручном сохранении ответа", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('/save-rag-instant')
    async def save_to_rag_instant(request: SaveRagRequest, fastapi_req: Request):
        """Мгновенное сохранение ответа: запись в JSON + векторизация в FAISS."""
        try:
            user_identifier, _, _, _ = await _extract_user_auth(fastapi_req)
            api_key = getattr(chat_model, 'api_key', '') or ''
            if not api_key:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()

            content_to_index = request.voice_text if request.voice_text.strip() else request.chat_text

            from src.ai.gemini.chat_response_store import save_approved_response
            save_success = await asyncio.to_thread(
                save_approved_response,
                user_identifier, request.query, request.chat_text, request.voice_text
            )

            from src.ai.gemini.user_query_rag import index_user_query
            rag_success = await asyncio.to_thread(
                index_user_query, user_identifier, api_key, request.query, content_to_index
            )

            if save_success and rag_success:
                return {"status": "success", "message": "Успешно сохранено в архив и проиндексировано в RAG"}
            elif save_success:
                return {"status": "success", "message": "Сохранено в архив, но произошла ошибка при индексации в RAG"}
            else:
                raise HTTPException(status_code=500, detail="Ошибка сохранения ответа")
        except Exception as e:
            logger.error("Ошибка при мгновенном сохранении в RAG", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('')
    async def chat(request: ChatRequest, fastapi_req: Request):
        """Processing of incoming chat message through plugins, user RAG context, AI model, and indexing."""
        from fastapi.responses import StreamingResponse
        import json

        async def event_generator():
            try:
                user_identifier, system_instruction, selected_model, settings = await _extract_user_auth(fastapi_req)

                api_key = getattr(chat_model, 'api_key', '') or ''
                if not api_key:
                    from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                    api_key = _get_gemini_api_key()

                # Извлечение RAG контекста
                user_context_str = ""
                skip_past_context = False
                clean_msg = request.message.strip().lower()
                if len(clean_msg) < 25:
                    control_words = {
                        'да', 'нет', 'yes', 'no', 'ок', 'ok', 'хочу', 'конечно',
                        'давай', 'проверь', 'найди', 'покажи', 'ладно', 'угу', 'yep', 'sure',
                        'want', 'check', 'find', 'show', 'okay', 'отлично',
                        'включи', 'запусти', 'play', 'start', 'open', 'открой', 'включай', 'запускай',
                        'поставь', 'вруби', 'воспроизведи', 'сейчас', 'now', 'go'
                    }
                    words = set(clean_msg.replace('!', ' ').replace('.', ' ').replace(',', ' ').split())
                    if words & control_words:
                        skip_past_context = True

                if api_key and user_identifier and len(request.message.strip()) >= 5 and not skip_past_context:
                    past_context = await asyncio.to_thread(
                        search_user_context, user_identifier, api_key, request.message, 2, 0.45
                    )
                    if past_context:
                        snippets = [item['text'] for item in past_context]
                        user_context_str = "\n[Контекст из предыдущих обсуждений]:\n" + "\n---\n".join(snippets)

                from src.user_manager.user_profile import get_recommendation_context
                pref_context = await asyncio.to_thread(get_recommendation_context, user_identifier)
                if pref_context:
                    user_context_str = f"{user_context_str}\n\n[Профиль предпочтений]:\n{pref_context}".strip()

                voice_gender_instruction = _get_voice_gender_rule(settings)

                # DEBUG MODE: Return full prompt without sending to model
                if request.generation_config.get('debug_mode', False):
                    debug_text = _build_debug_prompt(request, user_context_str, voice_gender_instruction)
                    yield f"data: {json.dumps({'status': 'DEBUG MODE: Промпт сформирован, не отправляется в модель'})}\n\n"
                    yield f"data: {json.dumps({'text': debug_text})}\n\n"
                    return

                # Check if request relates to media
                is_media = False
                rag_plugin = plugins.get('rag')
                if rag_plugin and hasattr(rag_plugin, '_is_media_query'):
                    if rag_plugin._is_media_query(request.message):
                        is_media = True
                    elif any(word in request.message.strip().lower().split() for word in _CONTEXT_CONTINUATION_WORDS) or len(request.message.strip()) < 15:
                        _history = request.history or []
                        last_model_text = ''
                        for entry in reversed(_history):
                            if entry.get('role') in ('model', 'assistant'):
                                parts = entry.get('parts', [])
                                last_model_text = ' '.join(
                                    p if isinstance(p, str) else p.get('text', '')
                                    for p in parts
                                )
                                break
                        if last_model_text and rag_plugin._is_media_query(last_model_text):
                            is_media = True

                # Check RAG configuration mode
                rag_mode = "rag+model"
                try:
                    from header import __root__
                    cfg_path = __root__ / 'config.json'
                    if cfg_path.exists():
                        with open(cfg_path, 'r', encoding='utf-8') as f:
                            cfg = json.load(f)
                            rag_mode = cfg.get("rag", {}).get("mode", "rag+model")
                except Exception:
                    pass

                # Dynamic context assembly
                dynamic_context_parts = []
                if voice_gender_instruction:
                    dynamic_context_parts.append(f"[Правило]: {voice_gender_instruction}")
                if user_context_str:
                    dynamic_context_parts.append(user_context_str)

                user_msg_with_context = request.message
                if dynamic_context_parts:
                    user_msg_with_context = "\n\n".join(dynamic_context_parts) + "\n\n[Запрос пользователя]:\n" + request.message

                token = fastapi_req.cookies.get('auth_token')
                from src.fastapi.router_control import get_room_id
                room_id = get_room_id(token, None)

                if request.generation_config.get('model'):
                    selected_model = request.generation_config['model']

                clean_history = _clean_chat_history(request.history)
                kwargs = {
                    'history': clean_history,
                    'room_id': room_id,
                    'model_name': selected_model,
                }
                if request.generation_config.get('search_engine'):
                    kwargs['search_engine'] = request.generation_config['search_engine']

                if selected_model:
                    active_model = get_chat_model(selected_model, None)
                    api_key = getattr(active_model, 'api_key', '') or getattr(chat_model, 'api_key', '') or ''
                else:
                    active_model = chat_model

                yield f"data: {json.dumps({'status': 'Проверка плагинов...'})}\n\n"

                full_response_text = ""
                chat_mode = request.generation_config.get('chat_mode', 'story')

                for plugin in plugins.values():
                    if chat_mode == 'story' and plugin.name == 'yt_dlp':
                        continue
                    if is_media and plugin.name != 'rag':
                        continue
                    if not is_media and plugin.name == 'rag':
                        continue

                    can_handle = False
                    if hasattr(plugin, 'can_handle') and plugin.can_handle(request.message):
                        can_handle = True
                    if not can_handle:
                        continue

                    plugin_name = plugin.__class__.__name__
                    yield f"data: {json.dumps({'status': f'Вызов плагина {plugin_name}...'})}\n\n"

                    plugin_kwargs = kwargs.copy()
                    plugin_kwargs['chat_mode'] = chat_mode
                    plugin_kwargs['dynamic_context'] = "\n\n".join(dynamic_context_parts) if dynamic_context_parts else ""
                    if request.generation_config.get('search_engine'):
                        plugin_kwargs['search_engine'] = request.generation_config['search_engine']

                    response = await plugin.handle(request.message, **plugin_kwargs)

                    import inspect
                    if inspect.isasyncgen(response):
                        has_text = False
                        has_voice = False
                        async for chunk in response:
                            if 'status' in chunk:
                                yield f"data: {json.dumps({'status': chunk['status']})}\n\n"
                            if 'text' in chunk and chunk['text'] is not None:
                                has_text = True
                                full_response_text += str(chunk['text'])
                                yield f"data: {json.dumps({'text': chunk['text']})}\n\n"
                            if 'voice' in chunk:
                                has_voice = True
                                yield f"data: {json.dumps({'voice': chunk['voice']})}\n\n"
                            if 'prompt_dump' in chunk:
                                yield f"data: {json.dumps({'prompt_dump': chunk['prompt_dump']})}\n\n"

                        if has_text:
                            if not has_voice and full_response_text:
                                yield f"data: {json.dumps({'status': 'Генерация голоса диктора...'})}\n\n"
                                chat_kwargs_2 = kwargs.copy()
                                chat_kwargs_2.pop('room_id', '')
                                chat_kwargs_2.pop('search_engine', None)
                                chat_kwargs_2['history'] = []
                                gen_cfg_2 = request.generation_config.copy()
                                gen_cfg_2['response_type'] = 'voice'
                                chat_kwargs_2['generation_config'] = gen_cfg_2

                                stream_generator_2 = narrator_model.chat_stream(full_response_text, **chat_kwargs_2)
                                async for v_chunk in stream_generator_2:
                                    if v_chunk:
                                        c = v_chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                                        if c:
                                            yield f"data: {json.dumps({'voice': c})}\n\n"

                            # Auto play film if tag present
                            film_title = await _try_auto_play_film(full_response_text, room_id)
                            if film_title:
                                yield f"data: {json.dumps({'status': f'▶ Запускаю: {film_title}'})}\n\n"

                            if full_response_text and api_key and user_identifier:
                                # Fire-and-forget: index in background, don't block the response
                                asyncio.ensure_future(asyncio.to_thread(
                                    index_user_query, user_identifier, api_key, request.message, full_response_text
                                ))
                            return
                        # Плагин ничего не нашёл — продолжаем к нативной модели
                    elif response:
                        full_response_text = str(response)
                        yield f"data: {json.dumps({'status': f'{plugin_name} вернул ответ', 'text': full_response_text})}\n\n"
                        if full_response_text and api_key and user_identifier:
                            asyncio.ensure_future(asyncio.to_thread(
                                index_user_query, user_identifier, api_key, request.message, full_response_text
                            ))
                        return

                if is_media:
                    yield f"data: {json.dumps({'status': 'Медиа не найдено в базе. Поиск в интернете...'})}\n\n"
                    # Модель имеет встроенный инструмент Google Search Grounding (types.GoogleSearch() в generative_ai.py),
                    # поэтому мы просто продолжаем генерацию. Модель сама найдет информацию в интернете.

                yield f"data: {json.dumps({'status': 'Генерация (этап 1)...'})}\n\n"
                
                chat_kwargs_1 = kwargs.copy()
                chat_kwargs_1.pop('room_id', '')
                chat_kwargs_1.pop('search_engine', None)
                gen_cfg_1 = request.generation_config.copy()
                gen_cfg_1['response_type'] = 'chat'
                chat_kwargs_1['generation_config'] = gen_cfg_1

                stream_generator_1 = active_model.chat_stream(user_msg_with_context, **chat_kwargs_1)
                
                chat_response = ""
                async for chunk in stream_generator_1:
                    if chunk:
                        c = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                        if c:
                            chat_response += c
                            yield f"data: {json.dumps({'text': c})}\n\n"
                
                voice_response = ""
                if chat_response:
                    yield f"data: {json.dumps({'status': 'Генерация (этап 2)...'})}\n\n"
                    
                    chat_kwargs_2 = kwargs.copy()
                    chat_kwargs_2.pop('room_id', '')
                    chat_kwargs_2.pop('search_engine', None)
                    chat_kwargs_2['history'] = []  # Narrator работает без истории
                    
                    gen_cfg_2 = request.generation_config.copy()
                    gen_cfg_2['response_type'] = 'voice'
                    chat_kwargs_2['generation_config'] = gen_cfg_2
                    
                    # На вход Narrator получает готовое каноническое описание от Chat
                    q2 = chat_response

                    stream_generator_2 = narrator_model.chat_stream(q2, **chat_kwargs_2)
                    async for chunk in stream_generator_2:
                        if chunk:
                            c = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                            if c:
                                voice_response += c
                                yield f"data: {json.dumps({'voice': c})}\n\n"
                
                full_response_text = chat_response

                # Автоматическая индексация успешного ответа в User RAG (fire-and-forget, не блокирует ответ)
                content_to_index = voice_response if voice_response.strip() else chat_response
                if content_to_index and api_key and user_identifier:
                    asyncio.ensure_future(asyncio.to_thread(
                        index_user_query, user_identifier, api_key, request.message, content_to_index
                    ))

            except Exception as ex:
                logger.error('Ошибка обработки чат-запроса', ex)
                yield f"data: {json.dumps({'error': str(ex)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return router

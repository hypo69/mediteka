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
import asyncio
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.logger import logger
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


def get_chat_model(selected_model_name: str, system_instruction: str = None):
    """Dynamically construct/retrieve the appropriate AI model instance."""
    is_gemini = selected_model_name.startswith('gemini-') or 'gemini' in selected_model_name.lower()
    
    if not is_gemini:
        from src.ai.foundry_chat import FoundryChatBase
        return FoundryChatBase(
            model_id=selected_model_name,
            system_prompt=system_instruction or "You are a helpful AI assistant.",
        )
    else:
        from src.ai.gemini.generative_ai import GoogleGenerativeAI
        _api_key_names = [n.strip() for n in os.getenv('GEMINI_API_KEY_NAMES', '').split(',') if n.strip()]
        return GoogleGenerativeAI(
            model_name=selected_model_name,
            api_key_names=_api_key_names,
            system_instruction=system_instruction,
            sleep_on_exhausted=False,
        )


def init_router(model, plugins: dict) -> APIRouter:
    """Инициализация роутера чата с привязкой модели и плагинов."""

    @router.get('/models')
    async def get_models() -> dict:
        """Получение списка доступных моделей."""
        import os
        use_foundry = os.getenv('USE_FOUNDRY', 'false').lower() in ('true', '1', 'yes')
        if use_foundry:
            foundry_model_id = os.getenv('FOUNDRY_MODEL_ID', 'qwen3-0.6b-generic-cpu:4')
            return {'models': [foundry_model_id]}
        else:
            from src.ai.gemini.generative_ai import _AVAILABLE_MODELS
            return {'models': _AVAILABLE_MODELS}

    @router.post('/code-helper')
    async def chat_code_helper(request: ChatRequest):
        """Чат помощника кода (разработчика) с использованием FAISS RAG."""
        try:
            from plugins.code_helper.rag.chat_interface import CodeHelperChat
            helper = CodeHelperChat()
            response_text = await helper.chat(request.message)
            return {"text": response_text}
        except Exception as e:
            logger.error("Ошибка чата Code Helper", e)
            raise HTTPException(status_code=500, detail=str(e))

    @router.post('')
    async def chat(request: ChatRequest, fastapi_req: Request):
        """Processing of incoming chat message through plugins, user RAG context, AI model, and indexing."""
        from fastapi.responses import StreamingResponse
        import json

        async def event_generator():
            try:
                system_instruction = None
                selected_model = None
                user_identifier = None
                settings = {}

                # Извлечение данных пользователя / IP для User RAG
                token = fastapi_req.cookies.get('auth_token')
                if token:
                    from src.fastapi.router_auth import verify_jwt_token
                    user_data = verify_jwt_token(token)
                    if user_data:
                        from src.user_manager import user_manager
                        # DB lookups are synchronous — run in thread pool
                        db_user = await asyncio.to_thread(user_manager.get_user_by_email, user_data.email)
                        if db_user:
                            user_identifier = db_user['id']
                            settings = await asyncio.to_thread(user_manager.get_user_settings, db_user['id'])
                            if settings:
                                if settings.get('system_instruction'):
                                    system_instruction = settings['system_instruction']
                                if settings.get('model'):
                                    selected_model = settings['model']

                if not user_identifier:
                    client_ip = fastapi_req.client.host if fastapi_req.client else 'unknown'
                    user_identifier = f"anon_{client_ip}"

                api_key = getattr(model, 'api_key', '') or ''
                # Default to model for fallback if no active_model set yet
                active_model = model
                if not api_key:
                    from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                    api_key = _get_gemini_api_key()

                # Извлекаем контекст из персонального RAG пользователя и из профиля предпочтений
                user_context_str = ""

                # Проверяем, нужно ли игнорировать старый контекст для простых управляющих слов/продолжений
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
                    # search_user_context makes a Gemini embedding HTTP call — run in thread pool
                    past_context = await asyncio.to_thread(
                        search_user_context, user_identifier, api_key, request.message, 2, 0.45
                    )
                    if past_context:
                        snippets = [item['text'] for item in past_context]
                        user_context_str = "\n[Контекст из предыдущих обсуждений пользователя]:\n" + "\n---\n".join(snippets)

                # Профиль предпочтений и просмотров для рекомендательной системы
                from src.user_manager.user_profile import get_recommendation_context
                pref_context = await asyncio.to_thread(get_recommendation_context, user_identifier)
                if pref_context:
                    user_context_str = f"{user_context_str}\n\n[Профиль предпочтений пользователя]:\n{pref_context}".strip()

                final_system_instruction = system_instruction or getattr(model, 'system_instruction', None)
                
                # Динамическая коррекция рода ответа под голос (если мужской -> женский род, если женский -> мужской род)
                voice_gender_instruction = ""
                tts_voice = settings.get('tts_voice', '') or os.getenv("TTS_VOICE", "ru-RU-DmitryNeural")
                voice_lower = tts_voice.lower()
                is_male_voice = any(name in voice_lower for name in ("dmitry", "yaraslaus", "male", "bayan", "aidar", "eugene", "georgy"))
                is_female_voice = any(name in voice_lower for name in ("svetlana", "elena", "female", "kseniya", "tanya", "aliona", "dariya"))
                if is_male_voice:
                    voice_gender_instruction = "IMPORTANT: Выбран мужской голос озвучки. Модель должна отвечать строго от женского лица (в женском роде, используя глаголы и местоимения женского рода: 'я пошла', 'я сделала' и т.д.)."
                elif is_female_voice:
                    voice_gender_instruction = "IMPORTANT: Выбран женский голос озвучки. Модель должна отвечать строго от мужского лица (в мужском роде, используя глаголы и местоимения мужского рода: 'я пошел', 'я сделал' и т.д.)."

                if voice_gender_instruction:
                    if final_system_instruction:
                        final_system_instruction = f"{final_system_instruction}\n\n{voice_gender_instruction}"
                    else:
                        final_system_instruction = voice_gender_instruction

                if user_context_str:
                    if final_system_instruction:
                        final_system_instruction = f"{final_system_instruction}\n\n{user_context_str}"
                    else:
                        final_system_instruction = user_context_str

                from src.fastapi.router_control import get_room_id
                room_id = get_room_id(token, None)
                kwargs = {
                    'system_instruction': final_system_instruction,
                    'history': request.history,
                    'room_id': room_id,
                }
                # Determine which model instance to use
                if selected_model:
                    active_model = get_chat_model(selected_model, final_system_instruction)
                    api_key = getattr(active_model, 'api_key', '') or getattr(model, 'api_key', '') or ''
                else:
                    active_model = model
                    if hasattr(active_model, 'system_instruction'):
                        active_model.system_instruction = final_system_instruction

                yield f"data: {json.dumps({'status': 'Проверка плагинов...'})}\n\n"

                # Проверяем, подходит ли запрос под медиа-плагин RAG.
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

                full_response_text = ""

                for plugin in plugins.values():
                    if plugin.name == 'rag' and not is_media:
                        continue
                    if is_media and plugin.name != 'rag':
                        continue

                    # Проверяем, может ли плагин обработать сообщение
                    if hasattr(plugin, 'can_handle') and not plugin.can_handle(request.message):
                        continue

                    plugin_name = plugin.__class__.__name__
                    yield f"data: {json.dumps({'status': f'Вызов плагина {plugin_name}...'})}\n\n"
                    response = await plugin.handle(request.message, **kwargs)

                    import inspect
                    if inspect.isasyncgen(response):
                        yielded_any = False
                        async for chunk in response:
                            yielded_any = True
                            if 'status' in chunk:
                                yield f"data: {json.dumps({'status': chunk['status']})}\n\n"
                            if 'text' in chunk:
                                full_response_text += chunk['text']
                                yield f"data: {json.dumps({'text': chunk['text']})}\n\n"
                            if 'voice' in chunk:
                                yield f"data: {json.dumps({'voice': chunk['voice']})}\n\n"

                        if yielded_any:
                            if full_response_text and api_key and user_identifier:
                                # Fire-and-forget: index in background, don't block the response
                                asyncio.ensure_future(asyncio.to_thread(
                                    index_user_query, user_identifier, api_key, request.message, full_response_text
                                ))
                            return
                    elif response:
                        full_response_text = str(response)
                        yield f"data: {json.dumps({'status': f'{plugin_name} вернул ответ', 'text': full_response_text})}\n\n"
                        if full_response_text and api_key and user_identifier:
                            asyncio.ensure_future(asyncio.to_thread(
                                index_user_query, user_identifier, api_key, request.message, full_response_text
                            ))
                        return

                if is_media:
                    yield f"data: {json.dumps({'error': 'Не удалось найти информацию в базе данных медиатеки'})}\n\n"
                    return

                yield f"data: {json.dumps({'status': 'Обращение к ИИ-модели...'})}\n\n"
                chat_kwargs = kwargs.copy()
                chat_kwargs.pop('room_id', None)
                chat_kwargs['generation_config'] = request.generation_config
                
                stream_generator = active_model.chat_stream(request.message, **chat_kwargs)
                buffer = ""
                current_channel = "text"
                
                async for chunk in stream_generator:
                    if not chunk:
                        continue
                    buffer += chunk
                    
                    if current_channel == "text":
                        if "[VOICE]" in buffer:
                            parts = buffer.split("[VOICE]", 1)
                            text_part = parts[0].replace("[CHAT]", "").strip()
                            if text_part:
                                full_response_text += text_part
                                yield f"data: {json.dumps({'text': text_part})}\n\n"
                            current_channel = "voice"
                            buffer = parts[1]
                        else:
                            if len(buffer) > 7:
                                output_len = len(buffer) - 7
                                to_output = buffer[:output_len].replace("[CHAT]", "")
                                if to_output:
                                    full_response_text += to_output
                                    yield f"data: {json.dumps({'text': to_output})}\n\n"
                                buffer = buffer[output_len:]
                    else:
                        clean_voice = chunk.replace("[VOICE]", "")
                        yield f"data: {json.dumps({'voice': clean_voice})}\n\n"
                
                # Выталкиваем остатки буфера
                if buffer:
                    if current_channel == "text":
                        to_output = buffer.replace("[CHAT]", "").strip()
                        if to_output:
                            full_response_text += to_output
                            yield f"data: {json.dumps({'text': to_output})}\n\n"
                    else:
                        to_output = buffer.replace("[VOICE]", "").strip()
                        if to_output:
                            yield f"data: {json.dumps({'voice': to_output})}\n\n"

                # Автоматическая индексация успешного ответа в User RAG (fire-and-forget, не блокирует ответ)
                if full_response_text and api_key and user_identifier:
                    asyncio.ensure_future(asyncio.to_thread(
                        index_user_query, user_identifier, api_key, request.message, full_response_text
                    ))

            except Exception as ex:
                logger.error('Ошибка обработки чат-запроса', ex)
                yield f"data: {json.dumps({'error': str(ex)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return router

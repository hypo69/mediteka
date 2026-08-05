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


class SaveRagRequest(BaseModel):
    query: str
    chat_text: str
    voice_text: str


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
        """Получение списка доступных моделей, сгруппированных по провайдеру."""
        from src.ai.gemini.generative_ai import _AVAILABLE_MODELS
        import os
        
        gemini_models = list(_AVAILABLE_MODELS)
        foundry_models = []
        
        use_foundry = os.getenv('USE_FOUNDRY', 'false').lower() in ('true', '1', 'yes')
        if use_foundry:
            foundry_model_id = os.getenv('FOUNDRY_MODEL_ID', 'qwen3-0.6b-generic-cpu:4')
            foundry_models.append(foundry_model_id)
            
        agy_models = ['agy-flash', 'agy-pro']
        
        return {
            'models': {
                'gemini': gemini_models,
                'foundry': foundry_models,
                'agy': agy_models
            }
        }

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

    @router.post('/save-rag')
    async def save_to_rag(request: SaveRagRequest, fastapi_req: Request):
        """Ручное сохранение ответа (текст + голос) в персональный RAG пользователя."""
        try:
            token = fastapi_req.cookies.get('auth_token')
            user_identifier = None
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

            api_key = getattr(model, 'api_key', '') or ''
            if not api_key:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()

            combined_response = f"Текст для чата:\n{request.chat_text}\n\nТекст для диктора:\n{request.voice_text}"

            success = await asyncio.to_thread(
                index_user_query, user_identifier, api_key, request.query, combined_response
            )
            
            if success:
                return {"status": "success", "message": "Успешно сохранено в RAG"}
            else:
                raise HTTPException(status_code=500, detail="Ошибка сохранения в RAG")
        except Exception as e:
            logger.error("Ошибка при ручном сохранении в RAG", e)
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

                # Извлекаем режим чата (story или download) из настроек запроса
                chat_mode = request.generation_config.get('chat_mode', 'story')

                for plugin in plugins.values():
                    # В режиме "сюжет" мы полностью пропускаем плагин yt-dlp (поиск/скачивание видео на YouTube)
                    if chat_mode == 'story' and plugin.name == 'yt_dlp':
                        continue

                    # Жесткая маршрутизация для RAG-плагина
                    if is_media and plugin.name != 'rag':
                        continue
                    if not is_media and plugin.name == 'rag':
                        continue

                    # Проверяем, может ли плагин обработать сообщение
                    can_handle = False
                    if hasattr(plugin, 'can_handle') and plugin.can_handle(request.message):
                        can_handle = True

                    if not can_handle:
                        continue

                    plugin_name = plugin.__class__.__name__
                    yield f"data: {json.dumps({'status': f'Вызов плагина {plugin_name}...'})}\n\n"
                    
                    # Передаем режим чата в параметры плагина
                    plugin_kwargs = kwargs.copy()
                    plugin_kwargs['chat_mode'] = chat_mode
                    response = await plugin.handle(request.message, **plugin_kwargs)

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

                is_rc = request.generation_config.get('is_rc', False)
                targets = ['voice', 'chat'] if is_rc else ['chat', 'voice']

                yield f"data: {json.dumps({'status': 'Генерация (этап 1)...'})}\n\n"
                
                chat_kwargs_1 = kwargs.copy()
                chat_kwargs_1.pop('room_id', None)
                gen_cfg_1 = request.generation_config.copy()
                gen_cfg_1['response_type'] = targets[0]
                chat_kwargs_1['generation_config'] = gen_cfg_1
                
                stream_generator_1 = active_model.chat_stream(request.message, **chat_kwargs_1)
                
                response_1 = ""
                key_1 = "voice" if targets[0] == "voice" else "text"
                async for chunk in stream_generator_1:
                    if chunk:
                        c = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                        if c:
                            response_1 += c
                            yield f"data: {json.dumps({key_1: c})}\n\n"
                
                if response_1:
                    yield f"data: {json.dumps({'status': 'Генерация (этап 2)...'})}\n\n"
                    
                    chat_kwargs_2 = kwargs.copy()
                    chat_kwargs_2.pop('room_id', None)
                    gen_cfg_2 = request.generation_config.copy()
                    gen_cfg_2['response_type'] = targets[1]
                    chat_kwargs_2['generation_config'] = gen_cfg_2
                    
                    q2 = f"{request.message}\n\nОпираясь на твой предыдущий ответ:\n{response_1}\n\nСгенерируй версию для {'диктора' if targets[1] == 'voice' else 'чата'}."
                    stream_generator_2 = active_model.chat_stream(q2, **chat_kwargs_2)
                    
                    response_2 = ""
                    key_2 = "voice" if targets[1] == "voice" else "text"
                    async for chunk in stream_generator_2:
                        if chunk:
                            c = chunk.replace("[CHAT]", "").replace("[VOICE]", "")
                            if c:
                                response_2 += c
                                yield f"data: {json.dumps({key_2: c})}\n\n"
                    
                    full_response_text = response_1 if targets[0] == 'chat' else response_2
                else:
                    full_response_text = ""

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

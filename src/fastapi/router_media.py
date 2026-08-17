# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI-роутер полного управления медиатекой и отслеживания просмотров
# =============================================================================

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.logger import logger
from src.utils.file import read_text_file, save_text_file
from src.secrets.api_key_state import load_api_keys, reset_exhausted, update_last_run
from src.ai import GoogleGenerativeAI
from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_organizer import (
    INSTRUCTION,
    OUTPUT_DIR,
    DEFAULT_CATEGORIES,
    MediaAuditor,
    MediaScanner,
    _normalize_disk_name,
    export_disk_md,
    export_disk_json,
    load_media_paths,
    DB_FILE,
)
from plugins.media_organizer.media_rag import build_media_rag
from plugins.media_organizer.core.series_collector import (
    collect,
    find_season_duplicates,
    check_integrity,
    build_report,
)
from src.user_manager.user_profile import (
    update_watch_progress,
    get_watch_progress,
    log_user_search,
    set_user_preference,
    load_user_profile
)

_ROOT = Path(__file__).parent.parent.parent
_REPORT_DIR = _ROOT / 'plugins' / 'media_organizer' / 'reports'
_REPORT_FILE = _REPORT_DIR / 'series_report.md'

_scan_state: dict = {'running': False, 'last': {}}


def _db(db_path: Path | None = None) -> MediaDatabase:
    return MediaDatabase(db_path or DB_FILE)


def _get_user_id(fastapi_req: Request) -> str:
    """Извлекает ID пользователя из авторизационного токена или IP."""
    token = fastapi_req.cookies.get('auth_token')
    if token:
        try:
            from src.fastapi.router_auth import verify_jwt_token
            user_data = verify_jwt_token(token)
            if user_data:
                from src.user_manager import user_manager
                db_user = user_manager.get_user_by_email(user_data.email)
                if db_user:
                    return str(db_user['id'])
        except Exception:
            pass

    client_ip = fastapi_req.client.host if fastapi_req.client else 'unknown'
    return f"anon_{client_ip}"


class ProgressUpdateRequest(BaseModel):
    file_path: str
    file_name: str
    current_time: float
    duration: float


class PreferenceRequest(BaseModel):
    title: str
    sentiment: str  # 'like' | 'dislike'
    genre: str = None
    category: str = None


class RagBuildRequest(BaseModel):
    key: str = ''
    directories: list[str] = []

class RagAddJsonRequest(BaseModel):
    documents: list[dict] = []
    key: str = ''

class RagSearchRequest(BaseModel):
    query: str = ''
    top_k: int = 10
    key: str = ''
    type: str = 'media'

class RagDocUpdateRequest(BaseModel):
    id: str
    query: str
    chat_text: str
    voice_text: str = ''



def init_router(prefix: str = '/api/media') -> APIRouter:
    router = APIRouter(prefix=prefix, tags=['media'])

    # ------------------------------------------------------------------
    # Storage availability
    # ------------------------------------------------------------------

    @router.get('/storage/available')
    async def get_available_storage() -> dict:
        """Получение списка доступных хранилищ с их путями."""
        from plugins.media_organizer.core.storage_manager import (
            load_active_storage, STORAGE_CONFIG
        )
        import json as _json
        active_paths = load_active_storage()
        disk_map = {}
        if STORAGE_CONFIG.exists():
            disk_map = _json.loads(STORAGE_CONFIG.read_text(encoding='utf-8'))
        return {
            'active_paths': active_paths,
            'all_configured': disk_map,
            'connected_count': len(active_paths),
            'total_count': len(disk_map),
        }

    @router.post('/storage/rescan')
    async def rescan_storage() -> dict:
        """Пересканирование доступных хранилищ и обновление списка активных путей."""
        from plugins.media_organizer.core.storage_manager import scan_and_save_active_storage
        active_paths = scan_and_save_active_storage()
        return {
            'status': 'ok',
            'active_paths': active_paths,
            'connected_count': len(active_paths),
        }

    # ------------------------------------------------------------------
    # User Profile / Watch Progress Endpoints
    # ------------------------------------------------------------------

    @router.post('/progress')
    async def save_progress(req: ProgressUpdateRequest, fastapi_req: Request):
        """Сохранение таймкода просмотренного видео для пользователя."""
        user_id = _get_user_id(fastapi_req)
        res = update_watch_progress(
            user_id=user_id,
            file_path=req.file_path,
            file_name=req.file_name,
            current_time=req.current_time,
            duration=req.duration
        )
        return {"status": "ok", "progress": res}

    @router.get('/progress')
    async def get_progress(file_path: str, fastapi_req: Request):
        """Получение сохранённого таймкода просмотренного видео."""
        user_id = _get_user_id(fastapi_req)
        res = get_watch_progress(user_id, file_path)
        return {"status": "ok", "progress": res}

    @router.get('/last-watched')
    async def get_last_watched(fastapi_req: Request):
        """Получение последнего воспроизведённого файла."""
        user_id = _get_user_id(fastapi_req)
        profile = load_user_profile(user_id)
        return {"status": "ok", "last_watched": profile.get("last_watched")}

    @router.post('/preference')
    async def save_preference(req: PreferenceRequest, fastapi_req: Request):
        """Сохранение лайка/дизлайка и предпочтений."""
        user_id = _get_user_id(fastapi_req)
        set_user_preference(
            user_id=user_id,
            title=req.title,
            sentiment=req.sentiment,
            genre=req.genre,
            category=req.category
        )
        return {"status": "ok"}

    @router.get('/profile')
    async def get_profile(fastapi_req: Request):
        """Получение всего профиля пользователя."""
        user_id = _get_user_id(fastapi_req)
        profile = load_user_profile(user_id)
        return {"status": "ok", "profile": profile}

    # ------------------------------------------------------------------
    # Scan & Admin
    # ------------------------------------------------------------------

    @router.post('/scan')
    async def start_scan(background_tasks: BackgroundTasks) -> dict:
        if _scan_state['running']:
            return {'status': 'running', 'message': 'Сканирование уже выполняется'}

        _scan_state['running'] = True

        def _do_scan():
            try:
                paths = load_media_paths()
                if not paths:
                    _scan_state['last'] = {'error': 'Медиа пути пусты'}
                    return
                scanner = MediaScanner(_db(), paths)
                scanner.scan_all()
                _scan_state['last'] = {'success': True}
            except Exception as ex:
                _scan_state['last'] = {'error': str(ex)}
            finally:
                _scan_state['running'] = False

        background_tasks.add_task(_do_scan)
        return {'status': 'started'}

    @router.get('/scan/status')
    async def get_scan_status() -> dict:
        return _scan_state

    # ------------------------------------------------------------------
    # By Category
    # ------------------------------------------------------------------

    @router.get('/by-category')
    async def get_media_by_category(fastapi_req: Request) -> dict:
        try:
            db = _db()
            records = db.export_all()
            
            categories_db = db.get_categories() if hasattr(db, 'get_categories') else None
            category_names = [c['name'] for c in categories_db] if categories_db else DEFAULT_CATEGORIES
            
            movies_by_category = {}
            series_by_category = {}
            
            for r in records:
                category = r.get('main_category') or 'Без категории'
                if category not in category_names:
                    category = 'Без категории'
                
                item = {
                    'name': r.get('title') or r.get('raw_name') or 'Без названия',
                    'title_ru': r.get('title_ru'),
                    'title_orig': r.get('title_orig'),
                    'media_type': r.get('media_type', 'movie'),
                    'type': r.get('media_type', 'movie'),
                    'disk_name': r.get('disk_name'),
                    'year': r.get('year'),
                    'path': r.get('path'),
                }
                
                if (r.get('media_type') or r.get('type')) == 'series':
                    if category not in series_by_category:
                        series_by_category[category] = []
                    series_by_category[category].append(item)
                else:
                    if category not in movies_by_category:
                        movies_by_category[category] = []
                    movies_by_category[category].append(item)
            
            return {
                'categories': category_names,
                'movies': movies_by_category,
                'series': series_by_category,
            }
        except Exception as e:
            return {'categories': [], 'movies': {}, 'series': {}, 'error': str(e)}

    # ------------------------------------------------------------------
    # Find media by title
    # ------------------------------------------------------------------

    @router.post('/by-title')
    async def find_media_by_title(req: dict, fastapi_req: Request) -> dict:
        title = req.get('title', '').strip()
        media_type = req.get('media_type') or req.get('type', '')

        if not title:
            raise HTTPException(status_code=400, detail='title required')

        # Логируем поиск пользователя
        user_id = _get_user_id(fastapi_req)
        log_user_search(user_id, title)

        db = _db()
        records = db.export_all()

        title_lower = title.lower()
        for record in records:
            r_title = record.get('title', '').lower()
            r_title_ru = (record.get('title_ru', '') or '').lower()
            r_title_orig = (record.get('title_orig', '') or '').lower()

            match = (
                title_lower == r_title or
                title_lower == r_title_ru or
                title_lower == r_title_orig or
                r_title.startswith(title_lower) or
                (r_title_ru and r_title_ru.startswith(title_lower)) or
                (r_title_orig and r_title_orig.startswith(title_lower))
            )

            if match:
                if media_type and (record.get('media_type') or record.get('type')) != media_type:
                    continue

                path = record.get('path', '')
                if not path:
                    continue

                return {
                    'title': record.get('title', ''),
                    'disk_name': record.get('disk_name', ''),
                    'media_type': record.get('media_type', ''),
                    'type': record.get('media_type', ''),
                    'year': record.get('year', ''),
                    'path': path,
                }

        return {'title': title, 'path': None, 'error': 'not found'}

    @router.get('/files')
    def list_media_files() -> list:
        """Получение списка всех медиафайлов для плеера."""
        try:
            db = _db()
            records = db.export_all()
            files = []
            for r in records:
                path = r.get('path', '')
                if path and Path(path).exists():
                    files.append({
                        'name': r.get('title', 'Unknown'),
                        'path': path,
                        'media_type': r.get('media_type', ''),
                        'type': r.get('media_type', ''),
                        'year': r.get('year', ''),
                    })
            return files
        except Exception as e:
            return []

    @router.get('/stream')
    async def stream_media(path: str) -> FileResponse:
        """Стриминг медиафайла по пути."""
        file_path = Path(path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail='File not found')
        return FileResponse(file_path, media_type='video/mp4')

    @router.get('/rag/status')
    async def get_rag_status_endpoint(type: str = 'media', fastapi_req: Request = Request) -> dict:
        """Получение статуса RAG-индекса и количества документов."""
        try:
            if type == 'chat':
                from src.ai.gemini.chat_response_store import list_responses
                from src.ai.gemini.user_query_rag import get_user_rag_stats
                
                # Получаем идентификатор пользователя
                user_identifier = ''
                if fastapi_req and fastapi_req != Request:
                    user_identifier = _get_user_id(fastapi_req)
                if not user_identifier:
                    user_identifier = 'anon_unknown'

                # Считаем количество сохраненных файлов JSON
                raw_responses = list_responses()
                user_responses = [r for r in raw_responses if r.get('user_id') == user_identifier]
                
                api_key = ''
                keys_file = Path(__file__).parent.parent / 'secrets' / 'gemini_keys.json'
                if keys_file.exists():
                    import json
                    keys_data = json.loads(keys_file.read_text(encoding='utf-8'))
                    for entry in keys_data.values():
                        if entry.get('status') == 'active' and entry.get('api_key'):
                            api_key = entry.get('api_key')
                            break
                if not api_key:
                    from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                    api_key = _get_gemini_api_key()
                
                rag_docs = 0
                if api_key:
                    try:
                        stats = get_user_rag_stats(user_identifier, api_key)
                        rag_docs = stats.get('count', 0)
                    except Exception as e:
                        logger.error(f"Error getting Chat RAG count: {e}")

                return {
                    "database": {
                        "total_records": len(raw_responses),
                        "by_type": {
                            "user_saved": len(user_responses),
                            "total_saved": len(raw_responses)
                        }
                    },
                    "rag_index": {
                        "documents": rag_docs
                    }
                }
            
            # По умолчанию: media RAG
            db = _db()
            records = db.export_all()
            movies_count = sum(1 for r in records if (r.get('media_type') or r.get('type')) == 'movie')
            series_count = sum(1 for r in records if (r.get('media_type') or r.get('type')) == 'series')
            total_records = movies_count + series_count
            
            from plugins.media_organizer.core.media_rag import get_media_rag
            api_key = ''
            keys_file = Path(__file__).parent.parent / 'secrets' / 'gemini_keys.json'
            if keys_file.exists():
                import json
                keys_data = json.loads(keys_file.read_text(encoding='utf-8'))
                for entry in keys_data.values():
                    if entry.get('status') == 'active' and entry.get('api_key'):
                        api_key = entry.get('api_key')
                        break
            if not api_key:
                try:
                    from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                    api_key = _get_gemini_api_key()
                except:
                    pass
                
            rag_docs = 0
            try:
                rag = get_media_rag(api_key)
                rag_docs = rag.count()
            except Exception as e:
                logger.error(f"Error getting RAG count: {e}")
                    
            return {
                "database": {
                    "total_records": total_records,
                    "by_type": {
                        "movie": movies_count,
                        "series": series_count
                    }
                },
                "rag_index": {
                    "documents": rag_docs
                }
            }
        except Exception as ex:
            logger.error(f"Error in RAG status: {ex}", exc_info=True)
            return {"database": {"total_records": 0, "by_type": {}}, "rag_index": {"documents": 0}, "error": str(ex)}

    @router.post('/rag/build')
    async def build_rag_endpoint(req: RagBuildRequest, type: str = 'media') -> dict:
        """Перестроение RAG-индекса."""
        try:
            api_key = ''
            if req.key:
                api_key = req.key
            else:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()

            if not api_key:
                raise HTTPException(status_code=400, detail='GEMINI_API_KEY не задан')

            if type == 'chat':
                from src.ai.gemini.user_query_rag import rebuild_all_user_rags
                rebuilt_count = rebuild_all_user_rags(api_key)
                return {'success': True, 'count': rebuilt_count}

            from plugins.media_organizer.core.media_rag import build_media_rag
            rag = await asyncio.to_thread(build_media_rag, api_key)
            return {'success': True, 'count': rag.count()}
        except HTTPException:
            raise
        except Exception as ex:
            logger.error(f'Error building RAG index: {ex}', exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/rag/search')
    async def search_rag_endpoint(
        req: RagSearchRequest = RagSearchRequest(),
        query: str = '',
        top_k: int = 10,
        key: str = '',
        type: str = 'media',
        fastapi_req: Request = Request
    ) -> dict:
        """Поиск по RAG-индексу."""
        try:
            search_query = (req.query or query).strip()
            search_top_k = req.top_k or top_k or 10
            search_key = req.key or key
            search_type = req.type if req.type != 'media' else (type or 'media')

            if not search_query:
                raise HTTPException(status_code=400, detail='Параметр query не может быть пустым')

            api_key = ''
            if search_key:
                keys_file = Path(__file__).parent.parent / 'secrets' / 'gemini_keys.json'
                if keys_file.exists():
                    try:
                        keys_data = json.loads(keys_file.read_text(encoding='utf-8'))
                        entry = keys_data.get(search_key)
                        if entry:
                            api_key = entry.get('api_key') or ''
                    except Exception:
                        pass
                if not api_key:
                    api_key = search_key

            if not api_key:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()

            if not api_key:
                raise HTTPException(status_code=400, detail='GEMINI_API_KEY не задан')

            if search_type == 'chat':
                user_identifier = ''
                if fastapi_req and fastapi_req != Request:
                    user_identifier = _get_user_id(fastapi_req)
                if not user_identifier:
                    user_identifier = 'anon_unknown'

                from src.ai.gemini.user_query_rag import search_user_context
                raw_results = search_user_context(user_identifier, api_key, search_query, top_k=search_top_k)
                formatted_results = []
                for item in raw_results:
                    meta = item.get('meta', {})
                    formatted_results.append({
                        "id": item.get('id', ''),
                        "score": item.get('score', 0),
                        "text": item.get('text', ''),
                        "title": meta.get('q', 'Диалог'),
                        "type": "chat_dialogue",
                        "year": meta.get('timestamp', '')
                    })
                return {"results": formatted_results}

            from plugins.media_organizer.core.media_rag import get_media_rag
            rag = get_media_rag(api_key)
            results = rag.search(search_query, top_k=search_top_k)
            formatted_results = []
            for item in results:
                meta = item.get('meta', {})
                m_type = meta.get('media_type') or meta.get('type') or 'movie'
                formatted_results.append({
                    "id": item.get('id', ''),
                    "score": item.get('score', 0),
                    "text": item.get('text', ''),
                    "title": meta.get('title', ''),
                    "media_type": m_type,
                    "type": m_type,
                    "year": meta.get('year', ''),
                    "disk_name": meta.get('disk_name', '')
                })
            return {"results": formatted_results}
        except HTTPException:
            raise
        except Exception as ex:
            logger.error(f"Error searching RAG index: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.get('/rag/documents')
    async def get_rag_documents_endpoint(
        query: str = '',
        limit: int = 50,
        offset: int = 0,
        type: str = 'media',
        fastapi_req: Request = Request
    ) -> dict:
        """Получение списка документов, проиндексированных в RAG, с возможностью фильтрации."""
        try:
            api_key = ''
            keys_file = Path(__file__).parent.parent / 'secrets' / 'gemini_keys.json'
            if keys_file.exists():
                import json
                keys_data = json.loads(keys_file.read_text(encoding='utf-8'))
                for entry in keys_data.values():
                    if entry.get('status') == 'active' and entry.get('api_key'):
                        api_key = entry.get('api_key')
                        break
            if not api_key:
                try:
                    from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                    api_key = _get_gemini_api_key()
                except:
                    pass

            if type == 'chat':
                user_identifier = ''
                if fastapi_req and fastapi_req != Request:
                    user_identifier = _get_user_id(fastapi_req)
                if not user_identifier:
                    user_identifier = 'anon_unknown'

                from src.ai.gemini.chat_response_store import list_responses
                raw_responses = list_responses(user_identifier)
                
                all_docs = []
                for item in raw_responses:
                    q = item.get('query', '')
                    ans = item.get('chat_text', '')
                    text = f"Пользователь спросил: {q}\nОтвет модели: {ans}"
                    doc_id = item.get('id', '')
                    
                    if query and query.lower() not in text.lower() and query.lower() not in doc_id.lower():
                        continue
                        
                    all_docs.append({
                        "id": doc_id,
                        "title": q,
                        "media_type": "chat_dialogue",
                        "type": "chat_dialogue",
                        "year": item.get('timestamp', '')[:16].replace('T', ' '),
                        "disk_name": "Файл JSON",
                        "text_preview": text[:300] + ('...' if len(text) > 300 else ''),
                        "text_full": text,
                        "query_raw": q,
                        "chat_text_raw": ans,
                        "voice_text_raw": item.get('voice_text', '')
                    })
                
                total = len(all_docs)
                paginated = all_docs[offset:offset+limit]
                return {
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "documents": paginated
                }

            # По умолчанию: media RAG
            from plugins.media_organizer.core.media_rag import get_media_rag
            rag = get_media_rag(api_key)
            
            all_docs = []
            for item in rag.metadatas:
                doc_id = item.get('id', '')
                text = item.get('text', '')
                meta = item.get('meta', {})
                
                # Фильтруем по подстроке, если она передана
                if query and query.lower() not in text.lower() and query.lower() not in doc_id.lower():
                    continue
                    
                m_type = meta.get('media_type') or meta.get('type', '')
                all_docs.append({
                    "id": doc_id,
                    "title": meta.get('title', doc_id.split('::')[-1] if '::' in doc_id else doc_id),
                    "media_type": m_type,
                    "type": m_type,
                    "year": meta.get('year', ''),
                    "disk_name": meta.get('disk_name', ''),
                    "text_preview": text[:300] + ('...' if len(text) > 300 else ''),
                    "text_full": text
                })
            
            total = len(all_docs)
            paginated = all_docs[offset:offset+limit]
            
            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "documents": paginated
            }
        except Exception as ex:
            logger.error(f"Error getting RAG documents: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/rag/documents/update')
    async def update_rag_document_endpoint(req: RagDocUpdateRequest) -> dict:
        """Обновление содержимого сохраненного RAG-документа на диске."""
        try:
            from src.ai.gemini.chat_response_store import update_response
            success = await asyncio.to_thread(
                update_response,
                req.id, req.query, req.chat_text, req.voice_text
            )
            if success:
                return {"status": "ok", "message": "Документ успешно обновлен"}
            else:
                raise HTTPException(status_code=404, detail="Документ не найден или ошибка записи")
        except Exception as ex:
            logger.error(f"Error updating RAG document: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/rag/documents/delete')
    async def delete_rag_document_endpoint(req: dict, fastapi_req: Request) -> dict:
        """Удаление сохраненного RAG-документа на диске (а также из FAISS индекса при type=chat)."""
        try:
            doc_id = req.get('id', '')
            doc_type = req.get('type', 'chat')
            if not doc_id:
                raise HTTPException(status_code=400, detail="ID документа обязателен")
            
            if doc_type == 'chat':
                from src.ai.gemini.chat_response_store import delete_response
                deleted_file = await asyncio.to_thread(delete_response, doc_id)
                
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()
                user_identifier = ''
                if fastapi_req:
                    user_identifier = _get_user_id(fastapi_req)
                if not user_identifier:
                    user_identifier = 'anon_unknown'
                
                if api_key:
                    from src.ai.gemini.user_query_rag import get_user_rag
                    user_rag = get_user_rag(user_identifier, api_key)
                    await asyncio.to_thread(user_rag.delete_document, doc_id)
                
                if deleted_file:
                    return {"status": "ok", "message": "Документ успешно удален"}
                else:
                    raise HTTPException(status_code=404, detail="Документ не найден или ошибка удаления")
            else:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()
                if api_key:
                    from plugins.media_organizer.core.media_rag import get_media_rag
                    rag = get_media_rag(api_key)
                    await asyncio.to_thread(rag.delete_document, doc_id)
                    return {"status": "ok", "message": "Документ успешно удален из медиа-RAG"}
                else:
                    raise HTTPException(status_code=400, detail="GEMINI_API_KEY не найден")
        except Exception as ex:
            logger.error(f"Error deleting RAG document: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/rag/clear')
    async def clear_rag_index_endpoint(req: dict, fastapi_req: Request) -> dict:
        """Очистка RAG-индекса (и сопутствующих файлов диалогов при type=chat)."""
        try:
            doc_type = req.get('type', 'media')
            
            api_key = ''
            keys_file = Path(__file__).parent.parent / 'secrets' / 'gemini_keys.json'
            if keys_file.exists():
                import json
                keys_data = json.loads(keys_file.read_text(encoding='utf-8'))
                for entry in keys_data.values():
                    if entry.get('status') == 'active' and entry.get('api_key'):
                        api_key = entry.get('api_key')
                        break
            if not api_key:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()
            if not api_key:
                raise HTTPException(status_code=400, detail="GEMINI_API_KEY не найден")

            if doc_type == 'chat':
                user_identifier = ''
                if fastapi_req and fastapi_req != Request:
                    user_identifier = _get_user_id(fastapi_req)
                if not user_identifier:
                    user_identifier = 'anon_unknown'
                
                # Удаляем файлы ответов чата для этого пользователя
                from src.ai.gemini.chat_response_store import _STORE_DIR
                deleted_count = 0
                for fp in _STORE_DIR.glob('*.json'):
                    try:
                        import json
                        entry = json.loads(fp.read_text(encoding='utf-8'))
                        if not user_identifier or entry.get('user_id') == str(user_identifier):
                            fp.unlink()
                            deleted_count += 1
                    except Exception as ex:
                        logger.error(f"[ChatResponseStore] Ошибка удаления при очистке {fp.name}", ex)

                # Очищаем индекс
                from src.ai.gemini.user_query_rag import get_user_rag
                user_rag = get_user_rag(user_identifier, api_key)
                await asyncio.to_thread(user_rag.clear)
                return {"status": "ok", "message": f"Очищено {deleted_count} файлов диалогов и RAG индекс"}
            else:
                from plugins.media_organizer.core.media_rag import get_media_rag
                rag = get_media_rag(api_key)
                await asyncio.to_thread(rag.clear)
                return {"status": "ok", "message": "Медиа-RAG индекс успешно очищен"}
        except Exception as ex:
            logger.error(f"Error clearing RAG index: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/audit')
    async def run_audit_endpoint() -> dict:
        """Запуск аудита медиатеки."""
        try:
            db = _db()
            from plugins.media_organizer.core.media_auditor import MediaAuditor
            auditor = MediaAuditor(db)
            issues = await auditor.audit()
            return {"status": "ok", "issues": issues}
        except Exception as ex:
            logger.error(f"Error running audit: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/rebuild')
    async def run_rebuild_endpoint() -> dict:
        """Восстановление (консолидация) БД."""
        try:
            from plugins.media_organizer.core.media_rebuild import rebuild_db
            db = _db()
            result_msg = rebuild_db(db)
            return {"status": "ok", "result": result_msg}
        except Exception as ex:
            logger.error(f"Error running rebuild: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/rag/add-json')
    async def add_json_to_rag(req: RagAddJsonRequest) -> dict:
        """Добавление произвольного JSON в RAG-индекс."""
        try:
            api_key = req.key
            if not api_key:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()
            if not api_key:
                raise HTTPException(status_code=400, detail="GEMINI_API_KEY не найден")
                
            from plugins.media_organizer.core.media_rag import get_media_rag
            rag = get_media_rag(api_key)
            
            if not req.documents:
                return {"status": "ok", "added": 0}
                
            valid_docs = []
            for doc in req.documents:
                if 'text' in doc:
                    valid_docs.append(doc)
                elif isinstance(doc, dict):
                    # Если text нет, попытаемся сериализовать весь dict в текст
                    text = " ".join(f"{k}: {v}" for k, v in doc.items() if v)
                    valid_docs.append({'text': text, 'meta': doc})
            
            if not valid_docs:
                raise HTTPException(status_code=400, detail="Не найдено валидных документов. JSON должен быть списком объектов.")

            added = rag.add_documents(valid_docs)
            return {"status": "ok", "added": len(valid_docs) if added else 0}
        except Exception as ex:
            logger.error(f"Error adding JSON to RAG: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/rag/add-json-dir')
    async def add_json_dir_to_rag(req: RagBuildRequest) -> dict:
        """Сканирование указанных директорий и добавление документов (JSON, TXT, MD) в RAG-индекс."""
        try:
            dirs_to_scan = req.directories if req.directories else [str(_ROOT / '.files_for_rag')]
            
            api_key = req.key
            if not api_key:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()
            if not api_key:
                raise HTTPException(status_code=400, detail="GEMINI_API_KEY не найден")
                
            from plugins.media_organizer.core.media_rag import get_media_rag
            rag = get_media_rag(api_key)
            
            total_added = 0
            processed_files = []
            
            for dir_path_str in dirs_to_scan:
                rag_dir = Path(dir_path_str)
                if not rag_dir.exists() or not rag_dir.is_dir():
                    logger.warning(f"Директория {rag_dir} не найдена или не является папкой.")
                    continue
                
                for file_path in rag_dir.rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in ('.json', '.txt', '.md'):
                        try:
                            try:
                                content = file_path.read_text(encoding='utf-8')
                            except UnicodeDecodeError:
                                content = file_path.read_text(encoding='cp1251', errors='replace')
                                
                            valid_docs = []
                            
                            if file_path.suffix.lower() == '.json':
                                try:
                                    data = json.loads(content)
                                    if not isinstance(data, list):
                                        if isinstance(data, dict):
                                            data = [data]
                                        else:
                                            continue
                                            
                                    for doc in data:
                                        if 'text' in doc:
                                            valid_docs.append(doc)
                                        elif isinstance(doc, dict):
                                            text = " ".join(f"{k}: {v}" for k, v in doc.items() if v)
                                            valid_docs.append({'text': text, 'meta': doc})
                                except Exception as e:
                                    logger.error(f"Error parsing JSON {file_path}: {e}")
                            else:
                                valid_docs.append({
                                    'id': f"{file_path.name}_{hash(content)}",
                                    'text': content,
                                    'meta': {
                                        'title': file_path.parent.name,
                                        'type': 'document',
                                        'disk_name': file_path.parent.name
                                    }
                                })
                                
                            if valid_docs:
                                added = rag.add_documents(valid_docs)
                                if added:
                                    total_added += len(valid_docs)
                                    processed_files.append(file_path.name)
                        except Exception as e:
                            logger.error(f"Error reading file {file_path}: {e}")
                            
            if not processed_files:
                 return {"status": "error", "message": "Не найдено файлов для добавления в указанных директориях. Проверьте кодировку или наличие файлов."}
                 
            return {"status": "ok", "added": total_added, "files": processed_files}
        except Exception as ex:
            logger.error(f"Error adding JSON dir to RAG: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    return router



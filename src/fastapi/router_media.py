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
    key: str | None = None

class RagAddJsonRequest(BaseModel):
    documents: list[dict]
    key: str | None = None



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
                    'type': r.get('type', 'movie'),
                    'disk_name': r.get('disk_name'),
                    'year': r.get('year'),
                    'path': r.get('path'),
                }
                
                if r.get('type') == 'series':
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
        media_type = req.get('type', '')

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
                if media_type and record.get('type') != media_type:
                    continue

                path = record.get('path', '')
                if not path:
                    continue

                return {
                    'title': record.get('title', ''),
                    'disk_name': record.get('disk_name', ''),
                    'type': record.get('type', ''),
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
                        'type': r.get('type', ''),
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
    async def get_rag_status_endpoint() -> dict:
        """Получение статуса RAG-индекса и количества документов."""
        try:
            db = _db()
            records = db.export_all()
            total_records = len(records)
            movies_count = sum(1 for r in records if r.get('type') != 'series')
            series_count = sum(1 for r in records if r.get('type') == 'series')
            
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
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()
                
            rag_docs = 0
            if api_key:
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
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/rag/build')
    async def build_rag_endpoint(req: RagBuildRequest) -> dict:
        """Перестроение RAG-индекса."""
        try:
            api_key = ''
            if req.key:
                keys_file = Path(__file__).parent.parent / 'secrets' / 'gemini_keys.json'
                if keys_file.exists():
                    import json
                    keys_data = json.loads(keys_file.read_text(encoding='utf-8'))
                    entry = keys_data.get(req.key)
                    if entry:
                        api_key = entry.get('api_key')
            
            if not api_key:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()
                
            if not api_key:
                raise HTTPException(status_code=400, detail="Gemini API key is not configured or not found.")
                
            from plugins.media_organizer.core.media_rag import build_media_rag
            rag = build_media_rag(api_key)
            count = rag.count()
            return {"success": True, "count": count}
        except Exception as ex:
            logger.error(f"Error building RAG index: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post('/rag/search')
    async def search_rag_endpoint(
        query: str,
        top_k: int = 10,
        key: str = ''
    ) -> dict:
        """Поиск по RAG-индексу."""
        try:
            api_key = ''
            if key:
                keys_file = Path(__file__).parent.parent / 'secrets' / 'gemini_keys.json'
                if keys_file.exists():
                    import json
                    keys_data = json.loads(keys_file.read_text(encoding='utf-8'))
                    entry = keys_data.get(key)
                    if entry:
                        api_key = entry.get('api_key')
                        
            if not api_key:
                from plugins.media_organizer.core.media_rag_functions import _get_gemini_api_key
                api_key = _get_gemini_api_key()
                
            if not api_key:
                raise HTTPException(status_code=400, detail="Gemini API key is not configured or not found.")
                
            from plugins.media_organizer.core.media_rag import get_media_rag
            rag = get_media_rag(api_key)
            if rag.count() == 0:
                return {"results": []}
                
            search_results = rag.search(query, top_k=top_k, threshold=0.3)
            
            formatted_results = []
            for r in search_results:
                meta = r.get('meta', {})
                formatted_results.append({
                    "title": meta.get('title', r.get('id', '').split('::')[-1] if '::' in r.get('id', '') else r.get('id', '')),
                    "type": meta.get('type', ''),
                    "category": meta.get('main_category', ''),
                    "year": meta.get('year', ''),
                    "disk_name": meta.get('disk_name', ''),
                    "score": r.get('score', 0.0)
                })
                
            return {"results": formatted_results}
        except Exception as ex:
            logger.error(f"Error searching RAG index: {ex}", exc_info=True)
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
        """Сканирование директории .files_for_rag и добавление JSON в RAG-индекс."""
        try:
            rag_dir = _ROOT / '.files_for_rag'
            if not rag_dir.exists() or not rag_dir.is_dir():
                return {"status": "error", "message": f"Папка .files_for_rag не найдена по пути: {rag_dir}"}

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
            
            for file_path in rag_dir.glob('*.json'):
                try:
                    content = file_path.read_text(encoding='utf-8')
                    data = json.loads(content)
                    
                    if not isinstance(data, list):
                        if isinstance(data, dict):
                            data = [data]
                        else:
                            continue
                            
                    valid_docs = []
                    for doc in data:
                        if 'text' in doc:
                            valid_docs.append(doc)
                        elif isinstance(doc, dict):
                            text = " ".join(f"{k}: {v}" for k, v in doc.items() if v)
                            valid_docs.append({'text': text, 'meta': doc})
                            
                    if valid_docs:
                        added = rag.add_documents(valid_docs)
                        if added:
                            total_added += len(valid_docs)
                            processed_files.append(file_path.name)
                except Exception as e:
                    logger.error(f"Error parsing RAG json file {file_path}: {e}")
                    
            return {"status": "ok", "added": total_added, "files": processed_files}
        except Exception as ex:
            logger.error(f"Error adding JSON dir to RAG: {ex}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(ex))

    return router



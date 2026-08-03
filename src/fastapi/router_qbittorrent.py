from __future__ import annotations
import json
import traceback
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from plugins.qbittorrent.qbittorrent import QBittorrentClient, relocate_missing, assign_categories_from_db
from plugins.media_organizer.database import MediaDatabase

_client: QBittorrentClient | None = None
_DIRS_FILE = Path(__file__).parent / "search_dirs.json"
_DB_FILE = Path(__file__).parent.parent.parent / "plugins" / "media_organizer" / "media.db"


def _reset_client():
    global _client
    _client = None


def _load_dirs() -> list[str]:
    try:
        return json.loads(_DIRS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_dirs(dirs: list[str]):
    _DIRS_FILE.write_text(json.dumps(dirs, ensure_ascii=False, indent=2), encoding="utf-8")


def init_router(ai_model=None) -> APIRouter:
    router = APIRouter(prefix="/api/torrents", tags=["torrents"])

    from src.utils.jjson import j_loads_ns
    _qbt_cfg = j_loads_ns(Path(__file__).parent.parent.parent / 'plugins' / 'qbittorrent' / 'config.json')

    def _get_client() -> QBittorrentClient:
        global _client
        if _client is None:
            print(f"[qbt] connecting to {_qbt_cfg.host}:{_qbt_cfg.port}")
            _client = QBittorrentClient(
                host=_qbt_cfg.host,
                port=int(_qbt_cfg.port),
                username=_qbt_cfg.username,
                password=_qbt_cfg.password,
            )
        return _client

    # ── search ────────────────────────────────────────────────────────────────

    @router.get("/search")
    async def search_torrents(query: str):
        if not query:
            raise HTTPException(status_code=400, detail="Query is empty")
        try:
            from plugins.torrent_playwright.playwright_searcher import PlaywrightTorrentSearcher
            searcher = PlaywrightTorrentSearcher(ai_model)
            results = await searcher.search(query)
            return results
        except Exception as ex:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(ex))

    # ── dirs ──────────────────────────────────────────────────────────────────

    @router.get("/dirs")
    def get_dirs():
        return _load_dirs()

    class DirsRequest(BaseModel):
        dirs: list[str]

    @router.post("/dirs")
    def save_dirs(req: DirsRequest):
        dirs = [d.strip() for d in req.dirs if d.strip()]
        _save_dirs(dirs)
        return dirs

    @router.delete("/dirs")
    def delete_dir(path: str):
        dirs = [d for d in _load_dirs() if d != path]
        _save_dirs(dirs)
        return dirs

    # ── torrents ──────────────────────────────────────────────────────────────

    @router.get("")
    def list_torrents():
        try:
            torrents = _get_client().torrents()
            return [
                {
                    "hash": t["hash"],
                    "name": t["name"],
                    "state": t.get("state", ""),
                    "progress": round(t.get("progress", 0) * 100, 1),
                    "size": t.get("size", 0),
                    "save_path": t.get("save_path", ""),
                }
                for t in torrents
            ]
        except Exception as ex:
            import requests
            if isinstance(ex, (ConnectionError, requests.exceptions.RequestException)):
                global _client
                _client = None  # сбросить чтобы следующий запрос попробовал снова
                raise HTTPException(status_code=503, detail=f"qBittorrent недоступен ({_qbt_cfg.host}:{_qbt_cfg.port}). Запустите qBittorrent и включите веб-интерфейс.")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post("/recheck/{torrent_hash}")
    def recheck(torrent_hash: str):
        try:
            _get_client().recheck(torrent_hash)
            return {"ok": True}
        except Exception as ex:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(ex))

    class RelocateRequest(BaseModel):
        dirs: list[str]

    @router.post("/relocate")
    def relocate(req: RelocateRequest):
        try:
            result = relocate_missing(_get_client(), req.dirs)
            return {"result": result}
        except Exception as ex:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(ex))

    class SetLocationRequest(BaseModel):
        hash: str
        location: str

    @router.post("/set-location")
    def set_location(req: SetLocationRequest):
        try:
            _get_client().set_location(req.hash, req.location)
            _get_client().recheck(req.hash)
            return {"ok": True}
        except Exception as ex:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(ex))

    @router.post("/assign-categories")
    def assign_categories():
        """Назначает категории торрентам на основе совпадений с БД медиатеки."""
        try:
            result = assign_categories_from_db(_get_client(), _DB_FILE)
            return {"result": result}
        except Exception as ex:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(ex))

    class DownloadRequest(BaseModel):
        url: str
        title: str
        source: str

    @router.post("/download")
    async def download(req: DownloadRequest):
        try:
            client = _get_client()
            if req.url.startswith("magnet:"):
                ok = client.add_torrent_by_url(req.url)
                if not ok:
                    raise HTTPException(status_code=500, detail="Failed to add magnet link to qBittorrent")
                return {"ok": True, "method": "magnet"}
            else:
                # Need to download .torrent file using Playwright first
                from plugins.torrent_playwright.playwright_searcher import PlaywrightTorrentSearcher
                searcher = PlaywrightTorrentSearcher()
                file_content = await searcher.download_torrent_file(req.source, req.url)
                if not file_content:
                    raise HTTPException(status_code=500, detail="Failed to download torrent file via Playwright")
                
                # Sanitize filename
                safe_title = "".join([c if c.isalnum() or c in "._-" else "_" for c in req.title])
                filename = f"{safe_title[:50]}.torrent"
                
                ok = client.add_torrent_by_file(file_content, filename)
                if not ok:
                    raise HTTPException(status_code=500, detail="Failed to add torrent file to qBittorrent")
                return {"ok": True, "method": "file"}
        except Exception as ex:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(ex))

    return router


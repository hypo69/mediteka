from .router_auth import init_router as init_auth_router
from .router_chat import init_router as init_chat_router
from .router_qbittorrent import init_router as init_qbt_router
from .router_media import init_router as init_media_admin_router
from .router_control import init_router as init_control_router
from .router_tts import init_router as init_tts_router

# Alias for backward compatibility
init_media_router = init_media_admin_router



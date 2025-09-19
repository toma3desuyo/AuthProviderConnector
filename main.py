"""
FastAPIアプリケーションエントリポイント

認証システムのメインアプリケーション
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from core.config import settings
from contexts.users.presentation.router import router as auth_router

# 日本時間でログを記録するカスタムフォーマッタ
class JSTFormatter(logging.Formatter):
    """日本時間（JST）でログを出力するフォーマッタ"""

    def formatTime(self, record, datefmt) -> str:
        """時刻を日本時間でフォーマット"""
        dt = datetime.fromtimestamp(record.created, tz=ZoneInfo('Asia/Tokyo'))
        return dt.strftime(datefmt)

# SimpleBucket形式のロギング設定（日本時間対応）
handler = logging.StreamHandler()
handler.setFormatter(
    JSTFormatter(
        fmt="%(levelname)s: %(asctime)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S JST"
    )
)

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler]
)

logger = logging.getLogger(__name__)

# FastAPIアプリケーションインスタンス
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version="1.0.0",
    debug=settings.debug,
)

# セッションミドルウェアを追加
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key
)

# ルーターを登録
app.include_router(
    auth_router,
    tags=["authentication"]
)

# アプリケーション起動時のログ
logger.info("Google Auth Sample starting up...")
logger.info("Google Auth Sample started successfully")

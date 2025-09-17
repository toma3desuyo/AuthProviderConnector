"""
FastAPIアプリケーションエントリポイント

認証システムのメインアプリケーション
"""
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from core.config import settings
from contexts.users.presentation.router import router as auth_router

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

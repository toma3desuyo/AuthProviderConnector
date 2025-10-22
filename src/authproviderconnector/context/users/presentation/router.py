"""ユーザー認証APIルーター."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response, Security, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings
from authproviderconnector.context.users.application.exception import (
    AccessTokenVerificationError,
    AuthenticatedUserNotFoundError,
    GetTokenFromProviderError,
    InternalTokenCreationError,
    LogoutURLGenerationError,
    MissingIdTokenError,
    TokenRefreshError,
)
from authproviderconnector.context.users.domain.exception import (
    AuthRedirectGenerationError,
)
from authproviderconnector.context.users.infrastructure.factory import UsersContext
from authproviderconnector.context.users.presentation.schema import (
    AuthenticatedUserResponse,
    DetailResponse,
    LogoutResponse,
    RefreshResponse,
)

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()


def _set_token_cookies(
    response: Response, access_token: str, refresh_token: str
) -> None:
    """共通のクッキー設定"""
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRATION_MINUTES * 60,
        path="/",
        secure=settings.is_production,
        httponly=False,
        samesite="lax",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRATION_DAYS * 24 * 60 * 60,
        path="/",
        secure=settings.is_production,
        httponly=True,
        samesite="lax",
    )


def _clear_token_cookies(response: Response) -> None:
    """認証関連クッキーを削除"""
    response.delete_cookie(
        key="access_token",
        path="/",
        secure=settings.is_production,
        httponly=False,
        samesite="lax",
    )
    response.delete_cookie(
        key="refresh_token",
        path="/",
        secure=settings.is_production,
        httponly=True,
        samesite="lax",
    )


LOGIN_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_302_FOUND: {
        "description": "認証プロバイダーへのリダイレクト",
        "headers": {
            "Location": {
                "description": "認証プロバイダの認証ページURL",
                "schema": {"type": "string"},
            },
            "Set-Cookie": {
                "description": "OAuth2フローのセキュリティを維持するためのセッションクッキー（state、nonceを含む）",
                "schema": {"type": "string"},
            },
        },
        "content": None,
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": DetailResponse,
        "description": "サーバー内部エラー",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": DetailResponse,
        "description": "リダイレクトURL生成エラー",
    },
}


CALLBACK_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_302_FOUND: {
        "description": "認証成功後にクライアントアプリへリダイレクト",
        "headers": {
            "Location": {
                "description": "リダイレクト先のクライアントアプリURL",
                "schema": {"type": "string"},
            },
            "Set-Cookie": {
                "description": "アクセストークンとリフレッシュトークンを格納したクッキー",
                "schema": {"type": "string"},
            },
        },
        "content": None,
    },
    status.HTTP_400_BAD_REQUEST: {
        "model": DetailResponse,
        "description": "認証失敗",
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": DetailResponse,
        "description": "サーバー内部エラー",
    },
    status.HTTP_503_SERVICE_UNAVAILABLE: {
        "model": DetailResponse,
        "description": "認証プロバイダにおける認証エラー",
    },
}


REFRESH_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_200_OK: {
        "description": "トークンリフレッシュ成功",
        "headers": {
            "Set-Cookie": {
                "description": "更新されたアクセストークンとリフレッシュトークンを格納したクッキー",
                "schema": {"type": "string"},
            },
        },
        "model": RefreshResponse,
    },
    status.HTTP_400_BAD_REQUEST: {
        "model": DetailResponse,
        "description": "不正なリクエスト",
    },
    status.HTTP_401_UNAUTHORIZED: {
        "model": DetailResponse,
        "description": "無効なリフレッシュトークン",
    },
}


LOGOUT_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": DetailResponse,
        "description": "ログアウトURLの返却に失敗",
    },
}


LOGOUT_CALLBACK_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_302_FOUND: {
        "description": "クライアントアプリへのリダイレクト",
        "headers": {
            "Location": {
                "description": "リダイレクト先のクライアントアプリURL",
                "schema": {"type": "string"},
            },
            "Set-Cookie": {
                "description": "アクセストークンとリフレッシュトークンを削除するクッキー",
                "schema": {"type": "string"},
            },
        },
        "content": None,
    },
}


ME_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": DetailResponse,
        "description": "アクセストークンが無効または期限切れ",
    },
    status.HTTP_404_NOT_FOUND: {
        "model": DetailResponse,
        "description": "ユーザーが存在しない",
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": DetailResponse,
        "description": "ユーザー情報取得中のエラー",
    },
}


def create_auth_router(users_context: UsersContext) -> APIRouter:
    """認証ルーターを作成"""
    router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

    @router.get(
        "/login",
        summary="ユーザーログイン",
        description="認証プロバイダを使用したGoogle OAuth2認証を開始します。",
        responses=LOGIN_RESPONSES,
        status_code=status.HTTP_302_FOUND,
    )
    async def login(
        request: Request,
    ) -> RedirectResponse:
        """ログインエンドポイント"""
        try:
            # ユースケース層でログイン処理を実行し、認証プロバイダのURLにリダイレクト
            return await users_context.login_usecase.execute(request)
        except AuthRedirectGenerationError as e:
            logger.error(f"Auth redirect generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail="リダイレクトURL生成に失敗しました。",
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during login: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail="ログイン処理中にエラーが発生しました。"
            ) from e

    @router.get(
        "/callback",
        summary="認証プロバイダからのコールバック",
        description="認証プロバイダからのリダイレクトを処理し、JWTトークンを発行します。",
        responses=CALLBACK_RESPONSES,
        status_code=status.HTTP_302_FOUND,
    )
    async def callback(
        request: Request,
        code: str = Query(..., description="認証プロバイダから返される認可コード"),
        state: str = Query(..., description="CSRF攻撃防止用のstateパラメータ"),
    ) -> RedirectResponse:
        """認証プロバイダのコールバックエンドポイント"""
        try:
            # ユースケース層でコールバックを処理
            access_token, refresh_token = await users_context.callback_usecase.execute(
                request
            )

            redirect_response = RedirectResponse(
                url=settings.CLIENT_APP_URL,
                status_code=status.HTTP_302_FOUND,
            )

            _set_token_cookies(
                response=redirect_response,
                access_token=access_token,
                refresh_token=refresh_token,
            )

            return redirect_response
        except (GetTokenFromProviderError, MissingIdTokenError) as e:
            logger.error(f"Provider authentication failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=503,  # Service Unavailable
                detail="認証に失敗しました。時間をおいて再度お試しください。",
            ) from e
        except InternalTokenCreationError as e:
            logger.error(f"Internal token creation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,  # Internal Server Error
                detail="認証トークンの生成処理中にエラーが発生しました。",
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during callback: {e}", exc_info=True)
            raise HTTPException(status_code=400, detail="認証に失敗しました。") from e

    @router.post(
        "/refresh",
        summary="トークンリフレッシュ",
        description="リフレッシュトークンを使用して新しいアクセストークンとリフレッシュトークンを取得します。",
        response_model=RefreshResponse,
        response_description="トークンリフレッシュ成功",
        responses=REFRESH_RESPONSES,
    )
    async def refresh_token(request: Request, response: Response) -> RefreshResponse:
        """トークンリフレッシュエンドポイント"""
        refresh_token = request.cookies.get("refresh_token")
        if refresh_token is None:
            logger.warning("Refresh token cookie is missing during refresh request.")
            raise HTTPException(
                status_code=400,
                detail="リフレッシュトークンが見つかりません。再度ログインしてください。",
            )
        try:
            # ユースケース層でリフレッシュ処理を実行
            new_access_token, new_refresh_token = (
                users_context.refresh_token_usecase.execute(refresh_token)
            )

            _set_token_cookies(
                response=response,
                access_token=new_access_token,
                refresh_token=new_refresh_token,
            )

            return RefreshResponse(message="トークンが正常に更新されました")
        except TokenRefreshError as e:
            logger.error(f"Token refresh failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=401,  # Unauthorized
                detail="リフレッシュトークンが無効です。再度ログインしてください。",
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
            raise HTTPException(
                status_code=400, detail="トークンの更新に失敗しました。"
            ) from e

    @router.get(
        "/me",
        summary="認証済みユーザー情報の取得",
        description="アクセストークンを検証し、ユーザー情報を返します。",
        response_model=AuthenticatedUserResponse,
        response_description="認証済みユーザー情報",
        responses=ME_RESPONSES,
    )
    async def get_authenticated_user(
        credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    ) -> AuthenticatedUserResponse:
        """アクセストークンに紐づくユーザー情報を返す"""
        token = credentials.credentials
        try:
            user = await users_context.get_authenticated_user_usecase.execute(token)
        except AccessTokenVerificationError as e:
            logger.warning("Access token verification failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=401,
                detail="アクセストークンが無効または期限切れです。refresh_tokenで再取得してください。",
            ) from e
        except AuthenticatedUserNotFoundError as e:
            logger.error("Authenticated user not found: {e}", exc_info=True)
            raise HTTPException(
                status_code=404,
                detail="ユーザーが見つかりませんでした。",
            ) from e
        except Exception as e:
            logger.error(
                "Unexpected error during getting user profile: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail="ユーザー情報の取得に失敗しました。",
            ) from e

        return AuthenticatedUserResponse(
            name=user.name,
            picture=user.picture,
        )

    @router.get(
        "/logout",
        summary="ユーザーログアウト",
        description="ユーザーをログアウトさせるために外部認証プロバイダのログアウトURLを返します。",
        response_model=LogoutResponse,
        response_description="ログアウトURL返却に成功",
        responses=LOGOUT_RESPONSES,
    )
    async def logout() -> LogoutResponse:
        """ログアウトエンドポイント"""
        try:
            # ユースケース層でログアウト処理を実行
            logout_info = users_context.logout_usecase.execute()

            return LogoutResponse(
                message=logout_info["message"], logout_url=logout_info["logout_url"]
            )
        except LogoutURLGenerationError as e:
            logger.error(f"Logout URL generation failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail="ログアウトURLの生成に失敗しました"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during logout: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail="ログアウト処理に失敗しました"
            ) from e

    @router.get(
        "/logout/callback",
        summary="ログアウト完了後の遷移先",
        description="認証クッキーを削除し、クライアントアプリにリダイレクトします。",
        responses=LOGOUT_CALLBACK_RESPONSES,
        status_code=status.HTTP_302_FOUND,
    )
    async def complete_logout() -> RedirectResponse:
        """ログアウト完了エンドポイント"""
        redirect_response = RedirectResponse(
            url=settings.CLIENT_APP_URL,
            status_code=status.HTTP_302_FOUND,
        )
        _clear_token_cookies(redirect_response)
        return redirect_response

    return router

"""
ユーザー認証APIルーター

認証関連のエンドポイントを定義
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from contexts.users.application.services import AuthenticationService
from contexts.users.application.dependencies import get_auth_service
from contexts.users.application.exceptions import (
    GetTokenFromProviderError,
    MissingIdTokenError,
    InternalTokenCreationError,
    TokenRefreshError,
    LogoutURLGenerationError
)
from contexts.users.domain.exceptions import AuthRedirectGenerationError
from schemas.auth import (
    TokenRefreshRequest,
    TokenResponse,
    LogoutResponse
)
from core.config import settings


router = APIRouter(prefix="/auth")


@router.get(
    "/login",
    summary="ユーザーログイン",
    description="認証プロバイダを使用したGoogle OAuth2認証を開始します。",
    responses={
        302: {
            "description": "認証プロバイダーへのリダイレクト",
            "headers": {
                "Location": {
                    "description": "認証プロバイダの認証ページURL",
                    "schema": {"type": "string"},
                },
                "Set-Cookie": {
                    "description": "OAuth2フローのセキュリティを維持するためのセッションクッキー（state、nonceを含む）",
                    "schema": {"type": "string"},
                }
            },
            "content": None,
        },
        500: {
            "description": "サーバー内部エラー",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "ログイン処理中にエラーが発生しました。"
                    }
                }
            }
        },
        503: {
            "description": "リダイレクトURL生成エラー",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "リダイレクトURL生成に失敗しました。"
                    }
                }
            }
        },
    },
    status_code=302
)
async def login(
    request: Request,
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> RedirectResponse:
    """ログインエンドポイント"""
    try:
        return await auth_service.get_login_redirect(request)
    except AuthRedirectGenerationError as e:
        raise HTTPException(
            status_code=503,  # Service Unavailable
            detail=f"リダイレクトURL生成に失敗しました。"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ログイン処理中にエラーが発生しました。"
        ) from e


@router.get(
    "/callback",
    summary="認証プロバイダからの認証コールバック",
    description="認証プロバイダからのリダイレクトを処理し、JWTトークンを発行します。",
    response_model=TokenResponse,
    responses={
        200: {
            "description": "認証成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ...",
                        "refresh_token": "eyJ...",
                        "token_type": "Bearer",
                        "expires_in": 900,
                        "message": "認証に成功しました。APIリクエストにはaccess_tokenをBearerトークンとして使用してください。"
                    }
                }
            }
        },
        400: {
            "description": "認証失敗",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "認証に失敗しました。"
                    }
                }
            }
        },
        422: {
            "description": "クエリパラメータのバリデーションエラー",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "missing",
                                "loc": ["query", "code"],
                                "msg": "Field required",
                                "input": None,
                            },
                            {
                                "type": "missing",
                                "loc": ["query", "state"],
                                "msg": "Field required",
                                "input": None,
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "サーバー内部エラー",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "認証トークンの生成処理中にエラーが発生しました。"
                    }
                }
            }
        },
        503: {
            "description": "認証プロバイダにおける認証エラー",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "認証に失敗しました。時間をおいて再度お試しください。"
                    }
                }
            }
        }
    },
)
async def callback(
    request: Request,
    code: str = Query(..., description="認証プロバイダから返される認可コード"),
    state: str = Query(..., description="CSRF攻撃防止用のstateパラメータ"),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> TokenResponse:
    """認証プロバイダのコールバックエンドポイント"""
    try:
        # アプリケーションサービス経由でコールバックを処理
        access_token, refresh_token = await auth_service.handle_callback(request)

        # トークンレスポンスを返す
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.access_token_expiration_minutes * 60,  # 秒単位
            message="認証に成功しました。APIリクエストにはaccess_tokenをBearerトークンとして使用してください。"
        )
    except (GetTokenFromProviderError, MissingIdTokenError) as e:
        raise HTTPException(
            status_code=503,  # Service Unavailable
            detail="認証に失敗しました。時間をおいて再度お試しください。"
        ) from e
    except InternalTokenCreationError as e:
        raise HTTPException(
            status_code=500,  # Internal Server Error
            detail="認証トークンの生成処理中にエラーが発生しました。"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"認証に失敗しました。") from e


@router.post(
    "/refresh",
    summary="トークンリフレッシュ",
    description="リフレッシュトークンを使用して新しいアクセストークンとリフレッシュトークンを取得します。",
    response_model=TokenResponse,
    responses={
        200: {
            "description": "トークンリフレッシュ成功",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ...",
                        "refresh_token": "eyJ...",
                        "token_type": "Bearer",
                        "expires_in": 900,
                        "message": "トークンが正常に更新されました"
                    }
                }
            }
        },
        400: {
            "description": "不正なリクエスト",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "トークンの更新に失敗しました"
                    }
                }
            }
        },
        401: {
            "description": "無効なリフレッシュトークン",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "リフレッシュトークンが無効です。再度ログインしてください。"
                    }
                }
            }
        },
        422: {
            "description": "リクエストボディのバリデーションエラー",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "missing",
                                "loc": ["body"],
                                "msg": "Field required",
                                "input": None,
                            }
                        ]
                    }
                }
            }
        }
    },
)
async def refresh_token(
    request: TokenRefreshRequest,
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> TokenResponse:
    """トークンリフレッシュエンドポイント"""
    try:
        # サービス層でリフレッシュ処理を実行
        new_access_token, new_refresh_token = auth_service.handle_refresh_token(
            request.refresh_token
        )

        # トークンレスポンスを返す
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=settings.access_token_expiration_minutes * 60,  # 秒単位
            message="トークンが正常に更新されました"
        )
    except TokenRefreshError as e:
        raise HTTPException(
            status_code=401,  # Unauthorized
            detail="リフレッシュトークンが無効です。再度ログインしてください。"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail="トークンの更新に失敗しました。"
        ) from e


@router.get(
    "/logout",
    summary="ユーザーログアウト",
    description="ユーザーをログアウトさせるために外部認証プロバイダのログアウトURLを返します。",
    response_model=LogoutResponse,
    responses={
        200: {
            "description": "ログアウトURLの返却に成功",
            "content": {
                "application/json": {
                    "example": {
                        "message": "ログアウトを完了するには、認証プロバイダにリダイレクトしてください",
                        "logout_url": "https://your-provider.example.com/v2/logout?returnTo=http://localhost:8000&client_id=your-client-id"
                    }
                }
            }
        },
        500: {
            "description": "ログアウトURLの返却に失敗",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "ログアウトURLの生成に失敗しました"
                    }
                }
            }
        }
    },
)
async def logout(
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> LogoutResponse:
    """ログアウトエンドポイント"""
    try:
        logout_info = auth_service.handle_logout()

        return LogoutResponse(
            message=logout_info["message"],
            logout_url=logout_info["logout_url"]
        )
    except LogoutURLGenerationError as e:
        raise HTTPException(
            status_code=500, detail="ログアウトURLの生成に失敗しました") from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="ログアウト処理に失敗しました") from e

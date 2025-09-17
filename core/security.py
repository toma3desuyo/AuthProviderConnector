"""
セキュリティ関連のコア機能

JWT トークンの生成・検証処理を提供
"""
from datetime import datetime, timedelta
from typing import Any
import jwt
from jwt.exceptions import (
    InvalidTokenError,
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    DecodeError
)
from core.config import settings
from contexts.users.domain.exceptions import (
    TokenExpiredError,
    InvalidTokenSignatureError,
    TokenDecodeError,
    InvalidTokenTypeError
)


def create_access_token(token_payload: dict[str, str]) -> str:
    """
    アクセストークンを作成

    Args:
        token_payload: ユーザーIDを含む辞書

    Returns:
        JWT アクセストークン
    """
    now = datetime.now()
    payload = {
        "sub": token_payload["user_id"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expiration_minutes)).timestamp()),
        "iss": settings.app_url,
        "aud": settings.app_url,
        "type": "access"
    }
    return jwt.encode(payload, settings.access_token_secret_key, algorithm=settings.internal_jwt_algorithm)


def create_refresh_token(token_payload: dict[str, Any]) -> str:
    """
    リフレッシュトークンを作成

    Args:
        token_payload: ユーザーIDを含む辞書

    Returns:
        JWT リフレッシュトークン
    """
    now = datetime.now()
    payload = {
        "sub": token_payload["user_id"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.refresh_token_expiration_days)).timestamp()),
        "iss": settings.app_url,
        "aud": settings.app_url,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.refresh_token_secret_key, algorithm=settings.internal_jwt_algorithm)


def verify_and_decode_refresh_token(token: str) -> dict[str, Any]:
    """
    リフレッシュトークンを検証してデコード

    Args:
        token: JWT リフレッシュトークン

    Returns:
        デコードされたペイロード

    Raises:
        TokenExpiredError: トークンの有効期限が切れている場合
        InvalidTokenSignatureError: トークンの署名が無効な場合
        TokenDecodeError: トークンのデコードに失敗した場合
        InvalidTokenTypeError: トークンタイプが正しくない場合
    """
    try:
        payload = jwt.decode(
            token,
            settings.refresh_token_secret_key,
            algorithms=[settings.internal_jwt_algorithm],
            audience=settings.app_url,
            issuer=settings.app_url
        )
    except ExpiredSignatureError as e:
        raise TokenExpiredError(f"リフレッシュトークンの有効期限が切れています: {str(e)}") from e
    except (InvalidAudienceError, InvalidIssuerError) as e:
        raise InvalidTokenSignatureError(f"リフレッシュトークンの署名検証に失敗しました: {str(e)}") from e
    except DecodeError as e:
        raise TokenDecodeError(f"リフレッシュトークンのデコードに失敗しました: {str(e)}") from e
    except InvalidTokenError as e:
        raise TokenDecodeError(f"無効なリフレッシュトークンです: {str(e)}") from e

    # トークンタイプの確認
    if payload.get("type") != "refresh":
        raise InvalidTokenTypeError("リフレッシュトークンのタイプが正しくありません")

    return payload

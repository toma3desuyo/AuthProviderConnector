"""
JWT関連のアプリケーションサービス

JWT トークンの生成・検証処理を提供
"""

from datetime import datetime, timedelta

import jwt
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
)

from config import settings
from authproviderconnector.context.users.domain.exception import (
    InvalidTokenSignatureError,
    InvalidTokenTypeError,
    TokenDecodeError,
    TokenExpiredError,
)
from authproviderconnector.context.users.types import InternalTokenData, TokenPayload


def create_access_token(token_payload: TokenPayload) -> str:
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
        "exp": int(
            (
                now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRATION_MINUTES)
            ).timestamp()
        ),
        "iss": f"{settings.api_base_url}{settings.base_redirect_path}",
        "aud": f"{settings.api_base_url}{settings.base_redirect_path}",
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.ACCESS_TOKEN_SECRET_KEY,
        algorithm=settings.INTERNAL_JWT_ALGORITHM,
    )


def create_refresh_token(token_payload: TokenPayload) -> str:
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
        "exp": int(
            (now + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)).timestamp()
        ),
        "iss": f"{settings.api_base_url}{settings.base_redirect_path}",
        "aud": f"{settings.api_base_url}{settings.base_redirect_path}",
        "type": "refresh",
    }
    return jwt.encode(
        payload,
        settings.REFRESH_TOKEN_SECRET_KEY,
        algorithm=settings.INTERNAL_JWT_ALGORITHM,
    )


def verify_and_decode_access_token(token: str) -> InternalTokenData:
    """アクセストークンを検証してデコード"""
    try:
        payload: InternalTokenData = jwt.decode(
            token,
            settings.ACCESS_TOKEN_SECRET_KEY,
            algorithms=[settings.INTERNAL_JWT_ALGORITHM],
            audience=f"{settings.api_base_url}{settings.base_redirect_path}",
            issuer=f"{settings.api_base_url}{settings.base_redirect_path}",
        )
    except ExpiredSignatureError as e:
        raise TokenExpiredError(
            f"アクセストークンの有効期限が切れています: {str(e)}"
        ) from e
    except (InvalidAudienceError, InvalidIssuerError) as e:
        raise InvalidTokenSignatureError(
            f"アクセストークンの署名検証に失敗しました: {str(e)}"
        ) from e
    except DecodeError as e:
        raise TokenDecodeError(
            f"アクセストークンのデコードに失敗しました: {str(e)}"
        ) from e
    except InvalidTokenError as e:
        raise TokenDecodeError(f"無効なアクセストークンです: {str(e)}") from e

    if payload.get("type") != "access":
        raise InvalidTokenTypeError("アクセストークンのタイプが正しくありません")

    return payload


def verify_and_decode_refresh_token(token: str) -> InternalTokenData:
    """
    リフレッシュトークンを検証してデコード

    Args:
        token: JWT リフレッシュトークン

    Returns:
        デコードされた内部トークンデータ

    Raises:
        TokenExpiredError: トークンの有効期限が切れている場合
        InvalidTokenSignatureError: トークンの署名が無効な場合
        TokenDecodeError: トークンのデコードに失敗した場合
        InvalidTokenTypeError: トークンタイプが正しくない場合
    """
    try:
        payload: InternalTokenData = jwt.decode(
            token,
            settings.REFRESH_TOKEN_SECRET_KEY,
            algorithms=[settings.INTERNAL_JWT_ALGORITHM],
            audience=f"{settings.api_base_url}{settings.base_redirect_path}",
            issuer=f"{settings.api_base_url}{settings.base_redirect_path}",
        )
    except ExpiredSignatureError as e:
        raise TokenExpiredError(
            f"リフレッシュトークンの有効期限が切れています: {str(e)}"
        ) from e
    except (InvalidAudienceError, InvalidIssuerError) as e:
        raise InvalidTokenSignatureError(
            f"リフレッシュトークンの署名検証に失敗しました: {str(e)}"
        ) from e
    except DecodeError as e:
        raise TokenDecodeError(
            f"リフレッシュトークンのデコードに失敗しました: {str(e)}"
        ) from e
    except InvalidTokenError as e:
        raise TokenDecodeError(f"無効なリフレッシュトークンです: {str(e)}") from e

    # トークンタイプの確認
    if payload.get("type") != "refresh":
        raise InvalidTokenTypeError("リフレッシュトークンのタイプが正しくありません")

    return payload

"""
ユーザーコンテキストで利用する型定義。

汎用的な dict[str, Any] の代わりに、ユーザーコンテキスト全体で使用する
構造化辞書を TypedDict で表現。
"""

from __future__ import annotations

from typing import TypedDict


class OAuthTokenData(TypedDict):
    """認証プロバイダ（Auth0）から取得するOAuthトークンデータ"""

    access_token: str
    id_token: str
    token_type: str  # 固定値 "Bearer"
    scope: str  # 例: "openid profile email"
    expires_in: int  # 秒数（例: 86400）
    expires_at: int  # Unixタイムスタンプ
    userinfo: UserInfo


class UserInfo(TypedDict):
    """OAuthプロバイダから取得するユーザー情報"""

    given_name: str
    family_name: str
    nickname: str
    name: str
    picture: str
    updated_at: str
    email: str
    email_verified: bool
    iss: str  # 発行者
    aud: str  # 対象（audience）
    sub: str  # サブジェクト（認証プロバイダ上のユーザーID）
    iat: int  # 発行時刻（Unixタイムスタンプ）
    exp: int  # 有効期限（Unixタイムスタンプ）
    sid: str  # セッションID
    nonce: str


class InternalTokenData(TypedDict):
    """内部トークンのデータ構造"""

    sub: str  # サブジェクト（アプリケーションレベルのユーザーID）
    iat: int  # 発行時刻（Unixタイムスタンプ）
    exp: int  # 有効期限（Unixタイムスタンプ）
    iss: str  # 発行者
    aud: str  # 対象（audience）
    type: str  # トークン種別（"access" または "refresh"）


class TokenPayload(TypedDict):
    """内部トークンのペイロード構造（メタデータ以外でトークンに含まれるコアの情報）"""

    user_id: str

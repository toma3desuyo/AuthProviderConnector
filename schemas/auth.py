"""
認証関連のPydanticスキーマ定義
"""
from pydantic import BaseModel, Field


class TokenRefreshRequest(BaseModel):
    """リフレッシュトークンリクエスト"""
    refresh_token: str = Field(..., description="リフレッシュトークン")


class TokenResponse(BaseModel):
    """トークンレスポンス"""
    access_token: str = Field(..., description="アクセストークン")
    refresh_token: str = Field(..., description="リフレッシュトークン")
    token_type: str = Field(..., description="トークンタイプ")
    expires_in: int = Field(..., description="有効期限（秒）")
    message: str = Field(..., description="メッセージ")

class LogoutResponse(BaseModel):
    """ログアウトレスポンス"""
    message: str = Field(..., description="メッセージ")
    logout_url: str = Field(..., description="外部認証プロバイダのログアウトURL")

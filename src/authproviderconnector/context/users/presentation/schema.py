"""認証関連のPydanticスキーマ定義"""

from pydantic import BaseModel, ConfigDict, Field


class RefreshResponse(BaseModel):
    """リフレッシュ処理のレスポンス"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "トークンが正常に更新されました",
            }
        }
    )

    message: str = Field(..., description="リフレッシュ結果のメッセージ")


class AuthenticatedUserResponse(BaseModel):
    """認証済みユーザー情報のレスポンス"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Simple Bucket",
                "picture": "https://example.com/avatar.png",
            }
        }
    )

    name: str = Field(..., description="ユーザー名")
    picture: str | None = Field(None, description="プロフィール画像URL")


class LogoutResponse(BaseModel):
    """ログアウトレスポンス"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "ログアウトを完了するには、認証プロバイダにリダイレクトしてください",
                "logout_url": "https://your-provider.example.com/v2/logout?returnTo=http://localhost:8000&client_id=your-client-id",
            }
        }
    )

    message: str = Field(..., description="メッセージ")
    logout_url: str = Field(..., description="外部認証プロバイダのログアウトURL")


class DetailResponse(BaseModel):
    """エラー時に返却されるdetailのみのレスポンス"""

    model_config = ConfigDict(
        json_schema_extra={"example": {"detail": "エラーメッセージ"}}
    )

    detail: str = Field(..., description="エラーメッセージ")

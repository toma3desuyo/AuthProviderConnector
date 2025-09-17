"""
アプリケーション設定管理

pydantic-settingsを使用して環境変数を型安全に管理
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""

    model_config = SettingsConfigDict()

    # アプリケーション基本設定
    app_name: str = "Auth0 JWT Google OAuth2 Sample"
    app_description: str = "FastAPI application with Auth0 Google authentication using JWT"
    app_url: str

    # Auth0設定
    auth0_domain: str
    auth0_client_id: str
    auth0_client_secret: str
    auth0_audience: str
    auth0_algorithm: str = "RS256"

    # アクセストークン設定
    access_token_secret_key: str
    internal_jwt_algorithm: str = "HS256"
    access_token_expiration_minutes: int

    # リフレッシュトークン設定
    refresh_token_secret_key: str
    refresh_token_expiration_days: int

    # セッションミドルウェア設定
    session_secret_key: str

    # データベース設定
    database_url: str

    # ログアウト設定
    logout_return_url: str

    # デバッグ設定
    debug: bool


    @property
    def auth0_issuer(self) -> str:
        """Auth0 Issuer URL"""
        return f"https://{self.auth0_domain}/"

    @property
    def auth0_jwks_url(self) -> str:
        """Auth0 JWKS URL"""
        return f"https://{self.auth0_domain}/.well-known/jwks.json"

    @property
    def auth0_openid_config_url(self) -> str:
        """Auth0 OpenID Configuration URL"""
        return f"https://{self.auth0_domain}/.well-known/openid-configuration"

# シングルトンインスタンス
settings = Settings()

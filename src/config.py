"""Application configuration module."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application level configuration."""

    ENVIRONMENT: str = Field("development", description="Runtime environment")

    DATABASE_URL: str = Field(
        "postgresql://postgres:postgres@postgres:5432/authconnector",
        description="Primary database URL",
    )

    DB_USE_NULL_POOL: bool = Field(False, description="Use SQLAlchemy NullPool")
    DB_POOL_SIZE: int | None = Field(None, description="Database pool size")
    DB_MAX_OVERFLOW: int | None = Field(
        None, description="Maximum overflow connections for the pool"
    )
    DB_POOL_TIMEOUT: int | None = Field(
        None, description="Pool acquire timeout (seconds)"
    )
    DB_POOL_RECYCLE: int | None = Field(
        None, description="Connection recycle window (seconds)"
    )
    DB_CONNECTION_TIMEOUT: int | None = Field(
        None, description="Connection timeout when opening a new connection"
    )
    DB_PREPARED_STATEMENT_CACHE_SIZE: int = Field(
        0, description="Prepared statement cache size"
    )
    DB_ECHO: bool = Field(False, description="Enable SQLAlchemy echo logging")
    DB_POOL_PRE_PING: bool = Field(False, description="Enable pool pre ping")

    CLIENT_APP_URL: str = Field(
        "http://localhost:5174",
        description="Frontend application base URL for redirects",
    )
    AUTH_PROVIDER_CONNECTOR_API_URL: str | None = Field(
        None, description="Public API base URL for redirect computations"
    )

    AUTH0_DOMAIN: str = Field("your-domain.auth0.com", description="Auth0 domain")
    AUTH0_CLIENT_ID: str = Field(
        "your-client-id", description="Auth0 client identifier"
    )
    AUTH0_CLIENT_SECRET: str = Field(
        "your-client-secret", description="Auth0 client secret"
    )
    AUTH0_AUDIENCE: str = Field("your-audience", description="Auth0 audience")
    AUTH0_ALGORITHM: str = Field("RS256", description="Auth0 JWT algorithm")

    ACCESS_TOKEN_SECRET_KEY: str = Field(
        "your-access-token-secret-key-change-in-production",
        description="Internal access token signing key",
    )
    REFRESH_TOKEN_SECRET_KEY: str = Field(
        "your-refresh-token-secret-key-change-in-production",
        description="Internal refresh token signing key",
    )
    INTERNAL_JWT_ALGORITHM: str = Field(
        "HS256", description="Internal JWT signing algorithm"
    )
    ACCESS_TOKEN_EXPIRATION_MINUTES: int = Field(
        15, description="Access token expiration window in minutes"
    )
    REFRESH_TOKEN_EXPIRATION_DAYS: int = Field(
        7, description="Refresh token expiration window in days"
    )

    SESSION_SECRET_KEY: str = Field(
        "your-session-secret-key-change-in-production",
        description="Session middleware secret key",
    )
    LOGOUT_RETURN_URL: str = Field(
        "http://localhost:5174/backend/api/v1/auth/logout/callback",
        description="Post logout redirect URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        """Return True when running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def api_base_url(self) -> str:
        """Return effective API base URL."""
        base = self.AUTH_PROVIDER_CONNECTOR_API_URL or "http://localhost:8000"
        return base.rstrip("/")

    @property
    def base_redirect_path(self) -> str:
        """Return redirect base path depending on environment."""
        if self.is_production:
            return "/backend"
        return ""

    @property
    def auth0_issuer(self) -> str:
        """Return Auth0 issuer URL."""
        return f"https://{self.AUTH0_DOMAIN}/"

    @property
    def auth0_jwks_url(self) -> str:
        """Return Auth0 JWKS endpoint."""
        return f"https://{self.AUTH0_DOMAIN}/.well-known/jwks.json"

    @property
    def auth0_openid_config_url(self) -> str:
        """Return Auth0 OpenID configuration endpoint."""
        return f"https://{self.AUTH0_DOMAIN}/.well-known/openid-configuration"


def create_settings() -> Settings:
    """Instantiate settings from environment."""
    return Settings()


settings = create_settings()

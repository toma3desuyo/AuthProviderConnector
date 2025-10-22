"""
Auth0 インフラストラクチャ層

Auth0との統合を管理し、OAuthフローとJWT検証を提供
"""

from uuid import uuid4

import jwt
from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from fastapi.responses import RedirectResponse
from jwt import PyJWKClient
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
    PyJWKClientError,
)

from config import settings
from authproviderconnector.context.users.application.port import IAuthClient
from authproviderconnector.context.users.domain.exception import (
    AuthRedirectGenerationError,
    InvalidTokenSignatureError,
    JWKSFetchError,
    MissingTokenClaimError,
    ProviderAuthenticationError,
    TokenDecodeError,
    TokenExpiredError,
)
from authproviderconnector.context.users.domain.model import User
from authproviderconnector.context.users.domain.repository import IUserRepository
from authproviderconnector.context.users.types import OAuthTokenData


class Auth0Client(IAuthClient):
    """Auth0クライアント"""

    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
        self.oauth = self._initialize_oauth()
        self.jwk_client = PyJWKClient(settings.auth0_jwks_url)

    def _initialize_oauth(self) -> OAuth:
        """OAuth クライアントを初期化"""
        oauth = OAuth()
        oauth.register(
            name="auth0",
            client_id=settings.AUTH0_CLIENT_ID,
            client_secret=settings.AUTH0_CLIENT_SECRET,
            server_metadata_url=settings.auth0_openid_config_url,
            client_kwargs={"scope": "openid profile email"},
        )
        return oauth

    async def get_authorization_redirect(
        self, request: Request, redirect_uri: str, connection: str
    ) -> RedirectResponse:
        """
        Auth0のログインページへのリダイレクトを生成

        Args:
            request: FastAPIのリクエストオブジェクト
            redirect_uri: コールバックURL
            connection: 接続タイプ（例: 'google-oauth2'）

        Returns:
            RedirectResponse: Auth0へのリダイレクト

        Raises:
            AuthRedirectGenerationError: リダイレクトURL生成に失敗した場合
        """
        try:
            redirect_response: RedirectResponse = (
                await self.oauth.auth0.authorize_redirect(
                    request, redirect_uri, connection=connection
                )
            )
            return redirect_response
        except Exception as e:
            raise AuthRedirectGenerationError(
                f"認証プロバイダへのリダイレクト生成に失敗しました: {str(e)}"
            ) from e

    async def get_token_from_provider(self, request: Request) -> OAuthTokenData:
        """
        Auth0からトークンを取得

        Args:
            request: FastAPIのリクエストオブジェクト

        Returns:
            OAuthTokenData: 認証トークン情報

        Raises:
            ProviderAuthenticationError: 認証プロバイダでの認証に失敗した場合
        """
        try:
            token_data: OAuthTokenData = await self.oauth.auth0.authorize_access_token(
                request
            )
            return token_data
        except Exception as e:
            raise ProviderAuthenticationError(
                "認証プロバイダでの認証に失敗しました。"
            ) from e

    async def verify_and_decode_token(self, id_token: str) -> User:
        """
        Auth0 IDトークンを検証してユーザーエンティティを生成（IAuthClientインターフェースの実装）
        既存ユーザーの検索・新規作成も含めて完全なUserエンティティを返す

        Args:
            id_token: Auth0から発行されたIDトークン

        Returns:
            User: 検証済みトークンから生成または取得されたユーザーエンティティ

        Raises:
            JWKSFetchError: 公開鍵の取得に失敗した場合
            TokenExpiredError: トークンの有効期限が切れている場合
            InvalidTokenSignatureError: トークンの署名が無効な場合
            TokenDecodeError: トークンのデコードに失敗した場合
            MissingTokenClaimError: 必須クレームが不足している場合
            DataIntegrityError: データ整合性エラーが発生した場合
            DatabaseConnectionError: データベース接続に失敗した場合
            UserSearchError: ユーザー検索に失敗した場合
            UserCreationError: ユーザー作成に失敗した場合
        """
        # PyJWKClientを使用して署名キーを取得(一度呼び出したらキャッシュされるため同期的に扱う)
        try:
            signing_key = self.jwk_client.get_signing_key_from_jwt(id_token)
        except PyJWKClientError as e:
            raise JWKSFetchError(f"公開鍵の取得に失敗しました: {str(e)}") from e

        # IDトークンを検証してデコード
        try:
            payload = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=[settings.AUTH0_ALGORITHM],
                audience=settings.AUTH0_AUDIENCE,
                issuer=settings.auth0_issuer,
            )
        except ExpiredSignatureError as e:
            raise TokenExpiredError(
                f"トークンの有効期限が切れています: {str(e)}"
            ) from e
        except (InvalidAudienceError, InvalidIssuerError) as e:
            raise InvalidTokenSignatureError(
                f"トークンの署名検証に失敗しました: {str(e)}"
            ) from e
        except (DecodeError, InvalidTokenError) as e:
            raise TokenDecodeError(f"トークンのデコードに失敗しました: {str(e)}") from e

        # 必須クレームの取得
        try:
            provider_user_id = payload["sub"]
            email = payload["email"]
            name = payload["name"]
        except KeyError as e:
            raise MissingTokenClaimError(
                f"必須クレームが不足しています: {str(e)}"
            ) from e
        picture = payload.get("picture")  # 任意クレーム

        # 既存ユーザーを検索
        user = await self.user_repository.find_by_linked_account(
            "auth0", provider_user_id
        )

        if not user:
            # 新規ユーザー作成
            user = User(id=uuid4(), email=email, name=name, picture=picture)
            # Auth0アカウントを紐付け
            user.add_linked_account("auth0", provider_user_id)
            # ユーザーを保存
            await self.user_repository.save(user)

        return user

"""
認証クライアントポートインターフェース

アプリケーション層で定義される外部認証プロバイダとの統合インターフェース
"""

from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.responses import RedirectResponse

from authproviderconnector.context.users.domain.model import User
from authproviderconnector.context.users.types import OAuthTokenData


class IAuthClient(ABC):
    """
    認証クライアントインターフェース

    外部認証プロバイダとの統合を抽象化
    """

    @abstractmethod
    async def get_authorization_redirect(
        self, request: Request, redirect_uri: str, connection: str
    ) -> RedirectResponse:
        """
        認証プロバイダのログインページへのリダイレクトを生成

        Args:
            request: FastAPIのリクエストオブジェクト
            redirect_uri: コールバックURL
            connection: 接続タイプ（例: 'google-oauth2'）

        Returns:
            RedirectResponse: 認証プロバイダへのリダイレクト

        Raises:
            AuthRedirectGenerationError: リダイレクトURL生成に失敗した場合
        """
        ...

    @abstractmethod
    async def get_token_from_provider(self, request: Request) -> OAuthTokenData:
        """
        認証プロバイダからトークンを取得

        Args:
            request: FastAPIのリクエストオブジェクト

        Returns:
            OAuthTokenData: 認証トークン情報

        Raises:
            ProviderAuthenticationError: 認証プロバイダでの認証に失敗した場合
        """
        ...

    @abstractmethod
    async def verify_and_decode_token(self, id_token: str) -> User:
        """
        認証プロバイダからのIDトークンを検証してユーザーエンティティを生成
        既存ユーザーの検索・新規作成も含めて完全なUserエンティティを返す

        Args:
            id_token: 検証するIDトークン

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
        ...

"""
ユーザー認証アプリケーションサービス

認証フローのビジネスロジックを実装
"""

from fastapi import Request
from fastapi.responses import RedirectResponse

from contexts.users.application.exceptions import (
    MissingIdTokenError,
    GetTokenFromProviderError,
    InternalTokenCreationError,
    TokenRefreshError,
    LogoutURLGenerationError
)
from contexts.users.domain.interfaces import IAuthClient
from contexts.users.domain.exceptions import (
    AuthRedirectGenerationError,
    ProviderAuthenticationError,
    TokenVerificationError,
    UserManagementError,
    InvalidTokenTypeError
)
from core.config import settings
from core.security import (
    create_access_token,
    create_refresh_token,
    verify_and_decode_refresh_token,
)


class AuthenticationService:
    """認証サービス"""

    def __init__(self, auth_client: IAuthClient):
        """
        コンストラクタ

        Args:
            auth_client: 認証クライアントの実装
        """
        self.auth_client = auth_client

    async def get_login_redirect(self, request: Request) -> RedirectResponse:
        """
        認証プロバイダのログインページへのリダイレクトを生成

        Args:
            request: FastAPIのリクエストオブジェクト

        Returns:
            RedirectResponse: 認証プロバイダへのリダイレクト情報

        Raises:
            AuthRedirectGenerationError: リダイレクトURL生成に失敗した場合
        """
        try:
            # 認証プロバイダへリダイレクト
            redirect_uri = f"{settings.app_url}/auth/callback"
            return await self.auth_client.get_authorization_redirect(
                request, redirect_uri, connection="google-oauth2"
            )
        except AuthRedirectGenerationError:
            raise
        except Exception as e:
            # 予期しないエラーをAuthRedirectGenerationErrorに変換
            raise AuthRedirectGenerationError(
                f"ログインリダイレクトの生成に失敗しました: {str(e)}"
            ) from e

    async def handle_callback(self, request: Request) -> tuple[str, str]:
        """
        認証プロバイダのコールバックを処理し、内部トークンを発行

        Args:
            request: FastAPIのリクエストオブジェクト

        Returns:
            (アクセストークン, リフレッシュトークン)のタプル

        Raises:
            GetTokenFromProviderError: 認証プロバイダーからトークン取得に失敗した場合
            MissingIdTokenError: 認証プロバイダからIDトークンが取得できなかった場合
            InternalTokenCreationError: トークン検証やユーザー処理、トークン生成に失敗した場合
        """
        # 認証プロバイダからトークンを取得
        try:
            token = await self.auth_client.get_token_from_provider(request)
        except ProviderAuthenticationError as e:
            raise GetTokenFromProviderError(
                f"認証プロバイダーからトークンを取得できませんでした: {str(e)}"
            ) from e

        # IDトークンを抽出
        try:
            id_token = token["id_token"]
        except KeyError as e:
            raise MissingIdTokenError(
                "認証プロバイダからのレスポンスにIDトークンが含まれていません"
            ) from e

        # IDトークンを検証して内部トークンを発行
        return await self._create_internal_tokens(id_token)

    async def _create_internal_tokens(self, id_token: str) -> tuple[str, str]:
        """
        認証プロバイダのIDトークンを検証し、内部トークンを発行

        Args:
            id_token: 認証プロバイダから受け取ったIDトークン

        Returns:
            (アクセストークン, リフレッシュトークン)のタプル

        Raises:
            InternalTokenCreationError: トークン検証やユーザー処理、トークン生成に失敗した場合
        """
        try:
            # IDトークンを検証してUserエンティティを取得
            user = self.auth_client.verify_and_decode_token(id_token)
        except TokenVerificationError as e:
            # トークン検証エラー（期限切れ、署名無効、デコード失敗など）
            raise InternalTokenCreationError(
                f"IDトークンの検証に失敗しました: {str(e)}"
            ) from e
        except UserManagementError as e:
            # ユーザー管理エラー（DB接続失敗、ユーザー作成/検索失敗など）
            raise InternalTokenCreationError(
                f"ユーザー情報の処理に失敗しました: {str(e)}"
            ) from e
        except Exception as e:
            # その他の予期しないエラー
            raise InternalTokenCreationError(
                f"内部トークンの生成に失敗しました: {str(e)}"
            ) from e

        # 内部トークンに含めるユーザー情報を取得
        token_payload = user.to_token_payload()

        # 内部トークンを生成
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        return access_token, refresh_token
        

    def handle_refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """
        リフレッシュトークンを使用して新しいトークンを発行

        Args:
            refresh_token: リフレッシュトークン

        Returns:
            (新しいアクセストークン, 新しいリフレッシュトークン)のタプル

        Raises:
            TokenRefreshError: リフレッシュトークンの検証や新しいトークンの生成に失敗した場合
        """
        try:
            # リフレッシュトークンを検証
            payload = verify_and_decode_refresh_token(refresh_token)
        except TokenVerificationError as e:
            # トークン検証エラー（期限切れ、署名無効、デコード失敗など）
            raise TokenRefreshError(
                f"リフレッシュトークンの検証に失敗しました: {str(e)}"
            ) from e
        except InvalidTokenTypeError as e:
            # トークンタイプエラー
            raise TokenRefreshError(
                f"リフレッシュトークンのタイプが正しくありません: {str(e)}"
            ) from e
        except Exception as e:
            # その他の予期しないエラー
            raise TokenRefreshError(
                f"トークンの更新に失敗しました: {str(e)}"
            ) from e
        
        # トークンペイロードを再構築
        try:
            token_payload = {
                "user_id": payload["sub"]
            }
        except KeyError as e:
            raise TokenRefreshError(
                f"生成されるリフレッシュトークンに含める情報が不足しています: {str(e)}"
            ) from e

        # 新しいトークンを生成
        new_access_token = create_access_token(token_payload)
        new_refresh_token = create_refresh_token(token_payload)

        return new_access_token, new_refresh_token

    def handle_logout(self) -> dict[str, str]:
        """
        ログアウト処理を実行

        Returns:
            ログアウト情報の辞書

        Raises:
            LogoutURLGenerationError: ログアウトURL生成に失敗した場合
        """
        try:
            # 外部認証プロバイダのログアウトURLを構築
            logout_url = (
                f"https://{settings.auth0_domain}/v2/logout?"
                f"returnTo={settings.logout_return_url}&client_id={settings.auth0_client_id}"
            )

            return {
                "message": "ログアウトを完了するには、認証プロバイダにリダイレクトしてください",
                "logout_url": logout_url
            }
        except Exception as e:
            # 予期しないエラーをLogoutURLGenerationErrorに変換
            raise LogoutURLGenerationError(
                f"ログアウトURLの生成に失敗しました: {str(e)}"
            ) from e

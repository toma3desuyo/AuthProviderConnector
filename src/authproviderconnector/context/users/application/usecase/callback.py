"""
コールバックユースケース

認証プロバイダからのコールバックを処理し、内部トークンを発行
"""

from fastapi import Request

from authproviderconnector.context.users.application.exception import (
    GetTokenFromProviderError,
    InternalTokenCreationError,
    MissingIdTokenError,
)
from authproviderconnector.context.users.application.jwt_service import (
    create_access_token,
    create_refresh_token,
)
from authproviderconnector.context.users.application.port import IAuthClient
from authproviderconnector.context.users.domain.exception import (
    ProviderAuthenticationError,
    TokenVerificationError,
    UserManagementError,
)


class CallbackUseCase:
    """コールバックユースケース"""

    def __init__(self, auth_client: IAuthClient):
        """
        コンストラクタ

        Args:
            auth_client: 認証クライアントの実装
        """
        self.auth_client = auth_client

    async def execute(self, request: Request) -> tuple[str, str]:
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
            user = await self.auth_client.verify_and_decode_token(id_token)
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

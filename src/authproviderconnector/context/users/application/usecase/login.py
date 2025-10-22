"""
ログインユースケース

認証プロバイダへのリダイレクトを処理
"""

from fastapi import Request
from fastapi.responses import RedirectResponse

from config import settings
from authproviderconnector.context.users.application.port import IAuthClient
from authproviderconnector.context.users.domain.exception import (
    AuthRedirectGenerationError,
)


class LoginUseCase:
    """ログインユースケース"""

    def __init__(self, auth_client: IAuthClient):
        """
        コンストラクタ

        Args:
            auth_client: 認証クライアントの実装
        """
        self.auth_client = auth_client

    async def execute(self, request: Request) -> RedirectResponse:
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
            api_base = settings.api_base_url
            redirect_uri = (
                f"{api_base}{settings.base_redirect_path}/api/v1/auth/callback"
            )
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

"""
ログアウトユースケース

ログアウト処理を実行
"""

from config import settings
from authproviderconnector.context.users.application.exception import (
    LogoutURLGenerationError,
)


class LogoutUseCase:
    """ログアウトユースケース"""

    def execute(self) -> dict[str, str]:
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
                f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
                f"returnTo={settings.LOGOUT_RETURN_URL}&client_id={settings.AUTH0_CLIENT_ID}"
            )

            return {
                "message": "ログアウトを完了するには、認証プロバイダにリダイレクトしてください",
                "logout_url": logout_url,
            }
        except Exception as e:
            # 予期しないエラーをLogoutURLGenerationErrorに変換
            raise LogoutURLGenerationError(
                f"ログアウトURLの生成に失敗しました: {str(e)}"
            ) from e

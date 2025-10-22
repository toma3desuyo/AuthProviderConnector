"""
リフレッシュトークンユースケース

リフレッシュトークンを使用して新しいトークンを発行
"""

from authproviderconnector.context.users.application.exception import TokenRefreshError
from authproviderconnector.context.users.application.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_and_decode_refresh_token,
)
from authproviderconnector.context.users.domain.exception import (
    InvalidTokenTypeError,
    TokenVerificationError,
)
from authproviderconnector.context.users.types import TokenPayload


class RefreshTokenUseCase:
    """リフレッシュトークンユースケース"""

    def execute(self, refresh_token: str) -> tuple[str, str]:
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
            raise TokenRefreshError(f"トークンの更新に失敗しました: {str(e)}") from e

        # トークンペイロードを再構築
        try:
            token_payload: TokenPayload = {"user_id": payload["sub"]}
        except KeyError as e:
            raise TokenRefreshError(
                f"生成されるリフレッシュトークンに含める情報が不足しています: {str(e)}"
            ) from e

        # 新しいトークンを生成
        new_access_token = create_access_token(token_payload)
        new_refresh_token = create_refresh_token(token_payload)

        return new_access_token, new_refresh_token

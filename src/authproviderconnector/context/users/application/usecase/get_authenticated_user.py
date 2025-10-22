"""アクセストークンから認証済みユーザーを取得するユースケース"""

from uuid import UUID

from authproviderconnector.context.users.application.exception import (
    AccessTokenVerificationError,
    AuthenticatedUserNotFoundError,
)
from authproviderconnector.context.users.application.jwt_service import (
    verify_and_decode_access_token,
)
from authproviderconnector.context.users.domain.exception import (
    TokenVerificationError,
    UserManagementError,
)
from authproviderconnector.context.users.domain.model import User
from authproviderconnector.context.users.domain.repository import IUserRepository


class GetAuthenticatedUserUseCase:
    """アクセストークンからユーザーを取得する"""

    def __init__(self, user_repository: IUserRepository) -> None:
        self.user_repository = user_repository

    async def execute(self, access_token: str) -> User:
        try:
            payload = verify_and_decode_access_token(access_token)
        except TokenVerificationError as e:
            raise AccessTokenVerificationError(
                "アクセストークンの検証に失敗しました"
            ) from e

        try:
            user_id = UUID(payload["sub"])
        except KeyError as e:
            raise AccessTokenVerificationError(
                "アクセストークンにユーザーIDが含まれていません"
            ) from e

        try:
            user = await self.user_repository.find_by_id(user_id)
        except UserManagementError as e:
            raise AccessTokenVerificationError(
                "ユーザー情報の取得に失敗しました"
            ) from e

        if user is None:
            raise AuthenticatedUserNotFoundError(
                f"指定されたユーザーが存在しません: {user_id}"
            )

        return user

"""Usersコンテキストのファクトリ

このコンテキストの依存関係の構築をカプセル化する
"""

from dataclasses import dataclass

from authproviderconnector.context.users.application.port import IAuthClient
from authproviderconnector.context.users.application.usecase.callback import (
    CallbackUseCase,
)
from authproviderconnector.context.users.application.usecase.get_authenticated_user import (
    GetAuthenticatedUserUseCase,
)
from authproviderconnector.context.users.application.usecase.login import LoginUseCase
from authproviderconnector.context.users.application.usecase.logout import LogoutUseCase
from authproviderconnector.context.users.application.usecase.refresh_token import (
    RefreshTokenUseCase,
)
from authproviderconnector.context.users.domain.repository import IUserRepository
from authproviderconnector.context.users.infrastructure.auth0_client import Auth0Client
from authproviderconnector.context.users.infrastructure.repository import (
    PostgreSQLUserRepository,
)
from infrastructure.db.connection import Database


@dataclass
class UsersContext:
    """Usersコンテキストのコンポーネント"""

    # Infrastructure
    user_repository: IUserRepository
    auth_client: IAuthClient

    # Application Use Cases
    login_usecase: LoginUseCase
    callback_usecase: CallbackUseCase
    refresh_token_usecase: RefreshTokenUseCase
    logout_usecase: LogoutUseCase
    get_authenticated_user_usecase: GetAuthenticatedUserUseCase


class UsersContextFactory:
    """Usersコンテキストのファクトリ"""

    @staticmethod
    def create(database: Database) -> UsersContext:
        """Usersコンテキストを構築

        Args:
            database: データベース接続オブジェクト

        Returns:
            UsersContext: 構築されたUsersコンテキスト
        """
        # リポジトリ（非同期データベースセッションファクトリーで初期化）
        user_repository: IUserRepository = PostgreSQLUserRepository(
            database.session_factory
        )

        # 認証クライアント
        auth_client: IAuthClient = Auth0Client(user_repository)

        # アプリケーションユースケース
        login_usecase = LoginUseCase(auth_client)
        callback_usecase = CallbackUseCase(auth_client)
        refresh_token_usecase = RefreshTokenUseCase()
        logout_usecase = LogoutUseCase()
        get_authenticated_user_usecase = GetAuthenticatedUserUseCase(user_repository)

        return UsersContext(
            user_repository=user_repository,
            auth_client=auth_client,
            login_usecase=login_usecase,
            callback_usecase=callback_usecase,
            refresh_token_usecase=refresh_token_usecase,
            logout_usecase=logout_usecase,
            get_authenticated_user_usecase=get_authenticated_user_usecase,
        )

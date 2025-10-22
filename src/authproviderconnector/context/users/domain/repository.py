"""
ユーザーリポジトリインターフェース

ドメイン層で定義されるユーザーアグリゲートの永続化インターフェース
"""

from abc import ABC, abstractmethod
from uuid import UUID

from authproviderconnector.context.users.domain.model import User


class IUserRepository(ABC):
    """
    ユーザーリポジトリインターフェース

    ユーザーアグリゲートの永続化を抽象化
    """

    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> User | None:
        """
        IDでユーザーを検索

        Args:
            user_id: ユーザーID

        Returns:
            ユーザーエンティティ（存在しない場合はNone）

        Raises:
            DatabaseConnectionError: データベース接続エラー
            UserSearchError: ユーザー検索エラー
        """
        ...

    @abstractmethod
    async def find_by_linked_account(
        self, provider_name: str, provider_user_id: str
    ) -> User | None:
        """
        連携されたアカウントでユーザーを検索

        Args:
            provider_name: プロバイダ名(例：'auth0', 'cognito')
            provider_user_id: プロバイダ上でのユーザーID

        Returns:
            ユーザーエンティティ（存在しない場合はNone）

        Raises:
            DatabaseConnectionError: データベース接続エラー
            UserSearchError: ユーザー検索エラー
        """
        ...

    @abstractmethod
    async def save(self, user: User) -> None:
        """
        ユーザーを保存

        Args:
            user: ユーザーエンティティ

        Raises:
            DatabaseConnectionError: データベース接続エラー
            DataIntegrityError: データ整合性エラー
            UserCreationError: ユーザー作成エラー
        """
        ...

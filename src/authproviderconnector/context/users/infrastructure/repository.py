"""
ユーザーリポジトリ実装

ユーザーアグリゲートの永続化実装
"""

from collections.abc import Callable
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import (
    IntegrityError,
    MissingGreenlet,
    OperationalError,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from authproviderconnector.context.users.domain.exception import (
    DatabaseConnectionError,
    DataIntegrityError,
    UserCreationError,
    UserSearchError,
    UserUpdateError,
)
from authproviderconnector.context.users.domain.model import LinkedAccount, User
from authproviderconnector.context.users.domain.repository import IUserRepository
from authproviderconnector.context.users.infrastructure.model import (
    LinkedAccountModel,
    UserModel,
)


class PostgreSQLUserRepository(IUserRepository):
    """
    PostgreSQLユーザーリポジトリ

    SQLAlchemyを使用したPostgreSQLへの永続化実装
    非同期セッションファクトリーを使用
    """

    session_factory: Callable[[], AsyncSession]

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        """
        リポジトリの初期化

        Args:
            session_factory: 非同期セッションファクトリー
        """
        self.session_factory = session_factory

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
        async with self.session_factory() as session:
            return await self._find_by_id_with_session(session, user_id)

    async def _find_by_id_with_session(
        self, session: AsyncSession, user_id: UUID
    ) -> User | None:
        """セッションを使ってIDでユーザーを検索"""
        try:
            stmt = (
                select(UserModel)
                .options(joinedload(UserModel.linked_accounts))
                .where(UserModel.id == user_id)
            )
            result = await session.execute(stmt)
            user_model = result.unique().scalar_one_or_none()

            if user_model:
                return self._to_domain_entity(user_model)
            return None
        except OperationalError as e:
            raise DatabaseConnectionError(
                f"データベース接続に失敗しました: {str(e)}"
            ) from e
        except SQLAlchemyError as e:
            raise UserSearchError(
                f"ユーザー検索中にエラーが発生しました: {str(e)}"
            ) from e

    async def find_by_linked_account(
        self, provider_name: str, provider_user_id: str
    ) -> User | None:
        """
        連携アカウントでユーザーを検索

        Args:
            provider_name: プロバイダ名
            provider_user_id: プロバイダ上でのユーザーID

        Returns:
            ユーザーエンティティ（存在しない場合はNone）

        Raises:
            DatabaseConnectionError: データベース接続エラー
            UserSearchError: ユーザー検索エラー
        """
        async with self.session_factory() as session:
            return await self._find_by_linked_account_with_session(
                session, provider_name, provider_user_id
            )

    async def _find_by_linked_account_with_session(
        self, session: AsyncSession, provider_name: str, provider_user_id: str
    ) -> User | None:
        """セッションを使って連携アカウントでユーザーを検索"""
        try:
            stmt = (
                select(UserModel)
                .join(LinkedAccountModel)
                .options(joinedload(UserModel.linked_accounts))
                .where(
                    LinkedAccountModel.provider_name == provider_name,
                    LinkedAccountModel.provider_user_id == provider_user_id,
                )
            )
            result = await session.execute(stmt)
            user_model = result.unique().scalar_one_or_none()

            if user_model:
                return self._to_domain_entity(user_model)
            return None
        except MissingGreenlet as e:
            raise UserSearchError(
                f"非同期処理のコンテキストエラーが発生しました。{str(e)}"
            ) from e
        except OperationalError as e:
            raise DatabaseConnectionError(
                f"データベース接続に失敗しました: {str(e)}"
            ) from e
        except SQLAlchemyError as e:
            raise UserSearchError(
                f"連携アカウント検索中にエラーが発生しました: {str(e)}"
            ) from e

    async def save(self, user: User) -> None:
        """
        ユーザーを保存

        Args:
            user: ユーザーエンティティ

        Raises:
            DatabaseConnectionError: データベース接続エラー
            DataIntegrityError: データ整合性エラー
            UserCreationError: ユーザー作成エラー
            UserUpdateError: ユーザー更新エラー
        """
        async with self.session_factory() as session:
            await self._save_with_session(session, user)
            await session.commit()

    async def _save_with_session(self, session: AsyncSession, user: User) -> None:
        """セッションを使ってユーザーを保存"""
        try:
            # 既存のユーザーを検索（linked_accountsも含めて）
            stmt = (
                select(UserModel)
                .options(joinedload(UserModel.linked_accounts))
                .where(UserModel.id == user.id)
            )
            result = await session.execute(stmt)
            user_model = result.unique().scalar_one_or_none()

            if user_model:
                # 既存ユーザーの更新
                user_model.email = user.email
                user_model.name = user.name
                user_model.picture = user.picture

                # 連携アカウントの差分同期
                await self._sync_linked_accounts(
                    session, user_model, user.linked_accounts
                )
            else:
                # 新規ユーザーの作成
                user_model = UserModel(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    picture=user.picture,
                )
                session.add(user_model)
                await (
                    session.flush()
                )  # ユーザーを先にフラッシュして外部キー制約を満たす

                # 連携アカウントを追加
                for account in user.linked_accounts:
                    linked_account_model = LinkedAccountModel(
                        id=uuid4(),
                        user_id=user.id,
                        provider_name=account.provider_name,
                        provider_user_id=account.provider_user_id,
                    )
                    session.add(linked_account_model)
        except IntegrityError as e:
            raise DataIntegrityError(
                f"データ整合性エラーが発生しました: {str(e)}"
            ) from e
        except OperationalError as e:
            raise DatabaseConnectionError(
                f"データベース接続に失敗しました: {str(e)}"
            ) from e
        except SQLAlchemyError as e:
            raise UserCreationError(
                f"ユーザー保存中にエラーが発生しました: {str(e)}"
            ) from e

    async def _sync_linked_accounts(
        self,
        session: AsyncSession,
        user_model: UserModel,
        new_accounts: list[LinkedAccount],
    ) -> None:
        """
        連携アカウントの差分同期

        既存のアカウントは保持し、新規追加と削除のみを行う

        Args:
            user_model: ユーザーモデル
            new_accounts: 新しい連携アカウントリスト

        Raises:
            DataIntegrityError: データ整合性エラー
            UserUpdateError: 連携アカウント同期エラー
        """
        try:
            # 現在の連携アカウントをキーでマッピング
            existing_accounts = {
                (acc.provider_name, acc.provider_user_id): acc
                for acc in user_model.linked_accounts
            }

            # 新しい連携アカウントをキーでマッピング
            new_accounts_map = {
                (acc.provider_name, acc.provider_user_id): acc for acc in new_accounts
            }

            # 削除対象を特定して削除
            for key, existing_acc in existing_accounts.items():
                if key not in new_accounts_map:
                    await session.delete(existing_acc)

            # 追加対象を特定して追加
            for key, new_acc in new_accounts_map.items():
                if key not in existing_accounts:
                    linked_account_model = LinkedAccountModel(
                        id=uuid4(),
                        user_id=user_model.id,
                        provider_name=new_acc.provider_name,
                        provider_user_id=new_acc.provider_user_id,
                    )
                    user_model.linked_accounts.append(linked_account_model)
        except IntegrityError as e:
            raise DataIntegrityError(
                f"連携アカウント同期中に整合性エラーが発生しました: {str(e)}"
            ) from e
        except SQLAlchemyError as e:
            raise UserUpdateError(
                f"連携アカウント同期中にエラーが発生しました: {str(e)}"
            ) from e

    def _to_domain_entity(self, user_model: UserModel) -> User:
        """
        データベースモデルからドメインエンティティへの変換

        Args:
            user_model: ユーザーモデル

        Returns:
            ユーザーエンティティ

        Raises:
            DuplicateLinkedAccountError: 同じプロバイダ名とプロバイダユーザーIDの組み合わせが既に存在する場合
        """
        # ユーザーエンティティを作成
        user = User(
            id=user_model.id,
            email=user_model.email,
            name=user_model.name,
            picture=user_model.picture,
        )

        # 連携アカウントを追加
        for linked_account_model in user_model.linked_accounts:
            user.add_linked_account(
                provider_name=linked_account_model.provider_name,
                provider_user_id=linked_account_model.provider_user_id,
            )

        return user

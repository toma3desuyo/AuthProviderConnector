"""
ユーザーリポジトリ実装

ユーザーアグリゲートの永続化実装
"""
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from contexts.users.domain.entities import User, LinkedAccount
from contexts.users.domain.interfaces import IUserRepository
from contexts.users.infrastructure.models import UserModel, LinkedAccountModel
from contexts.users.domain.exceptions import (
    UserSearchError,
    UserCreationError,
    UserUpdateError,
    DatabaseConnectionError,
    DataIntegrityError
)


class UserRepository(IUserRepository):
    """
    ユーザーリポジトリ

    SQLAlchemyを使用したデータベース永続化実装
    セッションは依存性注入により提供される
    """

    def __init__(self, session: Session):
        """
        リポジトリの初期化

        Args:
            session: SQLAlchemyセッション（依存性注入により提供）
        """
        self.session = session

    def find_by_id(self, user_id: UUID) -> User | None:
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
        try:
            user_model = self.session.query(UserModel).filter(
                UserModel.id == str(user_id)
            ).first()

            if user_model:
                return self._to_domain_entity(user_model)
            return None
        except OperationalError as e:
            raise DatabaseConnectionError(f"データベース接続に失敗しました: {str(e)}") from e
        except SQLAlchemyError as e:
            raise UserSearchError(f"ユーザー検索中にエラーが発生しました: {str(e)}") from e

    def find_by_linked_account(self, provider_name: str, provider_user_id: str) -> User | None:
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
        try:
            linked_account = self.session.query(LinkedAccountModel).filter(
                LinkedAccountModel.provider_name == provider_name,
                LinkedAccountModel.provider_user_id == provider_user_id
            ).first()

            if linked_account:
                user_model = linked_account.user
                return self._to_domain_entity(user_model)
            return None
        except OperationalError as e:
            raise DatabaseConnectionError(f"データベース接続に失敗しました: {str(e)}") from e
        except SQLAlchemyError as e:
            raise UserSearchError(f"連携アカウント検索中にエラーが発生しました: {str(e)}") from e

    def save(self, user: User) -> None:
        """
        ユーザーを保存

        Args:
            user: ユーザーエンティティ

        Raises:
            DatabaseConnectionError: データベース接続エラー
            DataIntegrityError: データ整合性エラー
            UserCreationError: ユーザー作成エラー
        """
        try:
            # 既存のユーザーを検索
            user_model = self.session.query(UserModel).filter(
                UserModel.id == str(user.id)
            ).first()
            # 既存ユーザーが見つかった場合、SQLAlchemyの追跡機能によって明示的にsessionに追加せずとも更新される
            if user_model:
                # 既存ユーザーの更新
                user_model.email = user.email
                user_model.name = user.name
                user_model.picture = user.picture

                # 連携アカウントの差分同期
                self._sync_linked_accounts(user_model, user.linked_accounts)
            else:
                # 新規ユーザーの作成
                user_model = UserModel(
                    id=str(user.id),
                    email=user.email,
                    name=user.name,
                    picture=user.picture
                )
                self.session.add(user_model)

                # 連携アカウントを追加
                for account in user.linked_accounts:
                    linked_account_model = LinkedAccountModel(
                        id=str(uuid4()),
                        user_id=str(user.id),
                        provider_name=account.provider_name,
                        provider_user_id=account.provider_user_id
                    )
                    self.session.add(linked_account_model)
        except IntegrityError as e:
            raise DataIntegrityError(f"データ整合性エラーが発生しました: {str(e)}") from e
        except OperationalError as e:
            raise DatabaseConnectionError(f"データベース接続に失敗しました: {str(e)}") from e
        except SQLAlchemyError as e:
            raise UserCreationError(f"ユーザー保存中にエラーが発生しました: {str(e)}") from e

    def _sync_linked_accounts(self, user_model: UserModel, new_accounts: list[LinkedAccount]) -> None:
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
                (acc.provider_name, acc.provider_user_id): acc
                for acc in new_accounts
            }

            # 削除対象を特定して削除
            for key, existing_acc in existing_accounts.items():
                if key not in new_accounts_map:
                    self.session.delete(existing_acc)

            # 追加対象を特定して追加
            for key, new_acc in new_accounts_map.items():
                if key not in existing_accounts:
                    linked_account_model = LinkedAccountModel(
                        id=str(uuid4()),
                        user_id=user_model.id,
                        provider_name=new_acc.provider_name,
                        provider_user_id=new_acc.provider_user_id
                    )
                    user_model.linked_accounts.append(linked_account_model)
        except IntegrityError as e:
            raise DataIntegrityError(f"連携アカウント同期中に整合性エラーが発生しました: {str(e)}") from e
        except SQLAlchemyError as e:
            raise UserUpdateError(f"連携アカウント同期中にエラーが発生しました: {str(e)}") from e

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
            id=UUID(user_model.id),
            email=user_model.email,
            name=user_model.name,
            picture=user_model.picture,
        )

        # 連携アカウントを追加
        for linked_account_model in user_model.linked_accounts:
            user.add_linked_account(
                provider_name=linked_account_model.provider_name,
                provider_user_id=linked_account_model.provider_user_id
            )

        return user

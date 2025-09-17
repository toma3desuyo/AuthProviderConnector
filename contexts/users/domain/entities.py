"""
ユーザーに関するエンティティ

ユーザーコンテキストのコアドメインモデル
"""
from dataclasses import dataclass, field
from uuid import UUID
from contexts.users.domain.exceptions import DuplicateLinkedAccountError


@dataclass(frozen=True)
class LinkedAccount:
    """
    連携アカウントエンティティ

    外部認証プロバイダ（ソーシャル、メール等）との紐付けを表現する子エンティティ
    """
    user_id: UUID  # 所属するユーザーのID
    provider_name: str  # 認証プロバイダ名 (例: 'auth0', 'cognito')
    provider_user_id: str  # プロバイダ上でのユーザーID (例: Auth0のsub)


@dataclass
class User:
    """
    ユーザーエンティティ（アグリゲートルート）

    ビジネスロジックのコアとなるユーザーモデル
    """
    id: UUID  # アプリケーション固有の不変ID
    email: str  # メールアドレス
    name: str  # ユーザー名
    picture: str | None = None  # プロフィール画像URL
    _linked_accounts: list[LinkedAccount] = field(default_factory=list)

    def add_linked_account(self, provider_name: str, provider_user_id: str) -> None:
        """
        連携アカウントを追加

        Args:
            provider_name: 認証プロバイダ名
            provider_user_id: プロバイダ上でのユーザーID

        Raises:
            DuplicateLinkedAccountError: 同じプロバイダ名とプロバイダユーザーIDの組み合わせが既に存在する場合
        """
        # 重複チェック
        for existing_account in self.linked_accounts:
            if (existing_account.provider_name == provider_name and
                existing_account.provider_user_id == provider_user_id):
                raise DuplicateLinkedAccountError(
                    f"連携アカウントが既に存在します: {provider_name}/{provider_user_id}"
                )

        linked_account = LinkedAccount(
            user_id=self.id,
            provider_name=provider_name,
            provider_user_id=provider_user_id
        )
        self._linked_accounts.append(linked_account)

    @property
    def linked_accounts(self) -> list[LinkedAccount]:
        """
        連携アカウントのリストを取得（読み取り専用）

        Returns:
            連携アカウントのリスト
        """
        return list(self._linked_accounts)

    def to_token_payload(self) -> dict:
        """
        トークンペイロード用の辞書に変換

        Returns:
            トークンペイロード用の辞書
        """
        return {
            "user_id": str(self.id),
        }

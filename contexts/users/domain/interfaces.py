"""
認証クライアントインターフェース

ドメイン層で定義される認証処理の抽象インターフェース
"""
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID
from fastapi import Request
from fastapi.responses import RedirectResponse
from contexts.users.domain.entities import User


class IUserRepository(ABC):
    """
    ユーザーリポジトリインターフェース
    
    ユーザーアグリゲートの永続化を抽象化
    """
    
    @abstractmethod
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
        pass

    @abstractmethod
    def find_by_linked_account(self, provider_name: str, provider_user_id: str) -> User | None:
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
        pass
    
    @abstractmethod
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
        pass
    


class IAuthClient(ABC):
    """
    認証クライアントインターフェース
    
    外部認証プロバイダとの統合を抽象化
    """
    
    @abstractmethod
    async def get_authorization_redirect(
        self, 
        request: Request, 
        redirect_uri: str,
        connection: str
    ) -> RedirectResponse:
        """
        認証プロバイダのログインページへのリダイレクトを生成
        
        Args:
            request: FastAPIのリクエストオブジェクト
            redirect_uri: コールバックURL
            connection: 接続タイプ（例: 'google-oauth2'）
            
        Returns:
            RedirectResponse: 認証プロバイダへのリダイレクト

        Raises:
            AuthRedirectGenerationError: リダイレクトURL生成に失敗した場合
        """
        pass
    
    @abstractmethod
    async def get_token_from_provider(self, request: Request) -> dict[str, Any]:
        """
        認証プロバイダからトークンを取得

        Args:
            request: FastAPIのリクエストオブジェクト

        Returns:
            dict[str, Any]: 認証トークン情報
            
        Raises:
            ProviderAuthenticationError: 認証プロバイダでの認証に失敗した場合
        """
        pass
    
    @abstractmethod
    def verify_and_decode_token(self, id_token: str) -> User:
        """
        認証プロバイダからのIDトークンを検証してユーザーエンティティを生成
        既存ユーザーの検索・新規作成も含めて完全なUserエンティティを返す
        
        Args:
            id_token: 検証するIDトークン
            
        Returns:
            User: 検証済みトークンから生成または取得されたユーザーエンティティ
            
        Raises:
            JWKSFetchError: 公開鍵の取得に失敗した場合
            TokenExpiredError: トークンの有効期限が切れている場合
            InvalidTokenSignatureError: トークンの署名が無効な場合
            TokenDecodeError: トークンのデコードに失敗した場合
            MissingTokenClaimError: 必須クレームが不足している場合
            DataIntegrityError: データ整合性エラーが発生した場合
            DatabaseConnectionError: データベース接続に失敗した場合
            UserSearchError: ユーザー検索に失敗した場合
            UserCreationError: ユーザー作成に失敗した場合
        """
        pass
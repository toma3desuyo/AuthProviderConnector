"""
FastAPI依存性注入

認証フローで使用する依存性を定義
"""
from fastapi import Depends
from sqlalchemy.orm import Session
from contexts.users.domain.interfaces import IAuthClient, IUserRepository
from contexts.users.application.services import AuthenticationService
from contexts.users.infrastructure.auth0_client import Auth0Client
from contexts.users.infrastructure.repositories import UserRepository
from contexts.users.infrastructure.database import get_db


def get_user_repository(db: Session = Depends(get_db)) -> IUserRepository:
    """
    ユーザーリポジトリを取得する

    Args:
        db: SQLAlchemyセッション

    Returns:
        IUserRepository: ユーザーリポジトリの実装
    """
    return UserRepository(db)


def get_auth_client(repository: IUserRepository = Depends(get_user_repository)) -> IAuthClient:
    """
    認証クライアントを取得する
    
    Args:
        repository: ユーザーリポジトリ
    
    Returns:
        IAuthClient: 認証クライアントの実装
    """
    return Auth0Client(repository)


def get_auth_service(auth_client: IAuthClient = Depends(get_auth_client)) -> AuthenticationService:
    """
    認証サービスを取得する
    
    Args:
        auth_client: 認証クライアント
        
    Returns:
        AuthenticationService: 認証サービスインスタンス
    """
    return AuthenticationService(auth_client)

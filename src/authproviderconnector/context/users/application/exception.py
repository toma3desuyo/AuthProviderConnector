"""
ユーザーに関するアプリケーション層例外

アプリケーション層での処理に関する例外を定義
"""


class GetTokenFromProviderError(Exception):
    """
    プロバイダーからのトークン取得エラー

    認証プロバイダーからトークンを取得する処理に失敗した場合にスローされる
    """

    pass


class MissingIdTokenError(Exception):
    """
    IDトークン欠落エラー

    認証プロバイダーからのレスポンスに
    IDトークンが含まれていない場合にスローされる
    """

    pass


class InternalTokenCreationError(Exception):
    """
    内部トークン生成エラー

    IDトークンの検証やユーザー情報の処理、
    内部トークンの生成に失敗した場合にスローされる
    """

    pass


class TokenRefreshError(Exception):
    """
    トークンリフレッシュエラー

    リフレッシュトークンの検証や新しいトークンの生成に
    失敗した場合にスローされる
    """

    pass


class LogoutURLGenerationError(Exception):
    """
    ログアウトURL生成エラー

    認証プロバイダへのログアウトURL生成に
    失敗した場合にスローされる
    """

    pass


class AccessTokenVerificationError(Exception):
    """アクセストークン検証エラー"""

    pass


class AuthenticatedUserNotFoundError(Exception):
    """アクセストークンと一致するユーザーが存在しない場合のエラー"""

    pass

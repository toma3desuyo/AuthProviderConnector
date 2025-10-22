"""
ユーザーに関するドメイン例外

ユーザーやトークンの処理に関するドメイン固有の例外を定義
"""


class AuthenticationError(Exception):
    """認証エラーの基底クラス"""

    pass


class ProviderAuthenticationError(AuthenticationError):
    """
    認証プロバイダでの認証エラー

    OAuth2プロバイダー（Auth0など）からのトークン取得や
    認証処理に失敗した場合にスローされる
    """

    pass


class AuthRedirectGenerationError(AuthenticationError):
    """
    リダイレクトURL生成エラー

    認証プロバイダへのリダイレクトURL生成が
    失敗した場合にスローされる
    """

    pass


# トークン検証関連のエラー
class TokenVerificationError(AuthenticationError):
    """トークン検証失敗の基底クラス"""

    pass


class InvalidTokenSignatureError(TokenVerificationError):
    """
    トークン署名検証エラー

    JWTの署名が無効、またはaudienceやissuerが
    期待値と一致しない場合にスローされる
    """

    pass


class TokenExpiredError(TokenVerificationError):
    """
    トークン有効期限切れエラー

    JWTの有効期限が切れている場合にスローされる
    """

    pass


class TokenDecodeError(TokenVerificationError):
    """
    トークンデコードエラー

    JWTのデコード処理自体が失敗した場合にスローされる
    """

    pass


class MissingTokenClaimError(TokenVerificationError):
    """
    必須クレーム欠落エラー

    JWTに必須のクレーム（sub, email, name等）が
    含まれていない場合にスローされる
    """

    pass


class InvalidTokenTypeError(TokenVerificationError):
    """
    無効なトークンタイプエラー

    JWTのtypeクレームが期待値と異なる場合にスローされる
    （例: refreshトークンが期待される場所でaccessトークンが使用された場合）
    """

    pass


class JWKSFetchError(TokenVerificationError):
    """
    公開鍵取得エラー

    JWKSエンドポイントから公開鍵を取得できない場合にスローされる
    """

    pass


# ユーザー管理関連のエラー
class UserManagementError(Exception):
    """ユーザー管理エラーの基底クラス"""

    pass


class UserSearchError(UserManagementError):
    """
    ユーザー検索エラー

    データベースからユーザーを検索する際に
    エラーが発生した場合にスローされる
    """

    pass


class UserCreationError(UserManagementError):
    """
    ユーザー作成エラー

    新規ユーザーの作成・保存に失敗した場合にスローされる
    """

    pass


class UserUpdateError(UserManagementError):
    """
    ユーザー更新エラー

    既存ユーザーの更新・保存に失敗した場合にスローされる
    """

    pass


class DatabaseConnectionError(UserManagementError):
    """
    データベース接続エラー

    データベースへの接続が失敗した場合にスローされる
    """

    pass


class DataIntegrityError(UserManagementError):
    """
    データ整合性エラー

    データベースの整合性制約違反が発生した場合にスローされる
    """

    pass


class DuplicateLinkedAccountError(UserManagementError):
    """
    重複連携アカウントエラー

    同じプロバイダ名と プロバイダユーザーIDの組み合わせで
    連携アカウントを追加しようとした場合にスローされる
    """

    pass

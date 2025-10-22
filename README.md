# AuthProviderConnector

AuthProviderConnector は Auth0 を利用した Google OAuth2 認証フローを提供する FastAPI ベースのバックエンドです。

## 主な機能
- Auth0 (Google) を用いたログイン / コールバック / リフレッシュ / ログアウト API
- 内部 JWT (アクセストークン / リフレッシュトークン) の発行と検証
- PostgreSQL ベースのユーザー永続化層
- Alembic によるマイグレーション管理
- `uv` ベースの依存管理と Docker / Dev Container サポート

## Docker コンテナ
- `api` : FastAPI アプリケーション (`uv run up`)
- `postgres` : 永続化用 PostgreSQL

## Dev Container
`.devcontainer` フォルダに VS Code Dev Container 構成を同梱しています。`Dev Containers: Open Folder in Container...` から利用できます。

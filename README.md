# AuthProviderConnector

AuthProviderConnector は Auth0 を用いて Google OAuth2 認証フローを提供し、発行した内部 JWT を通じてクライアントとセッションを共有する FastAPI ベースのバックエンドです。PostgreSQL にユーザー / 連携アカウント情報を永続化し、Alembic を使ったマイグレーションと `uv` を使ったモダンなパッケージ管理を採用しています。

## 主な機能
- `/api/v1/auth` 配下でのログイン開始、コールバック処理、トークンリフレッシュ、ユーザー情報取得、ログアウト URL 返却、ログアウト完了ハンドラ
- Auth0 から受け取った ID トークンの検証後、内部アクセストークン / リフレッシュトークン（JWT）を発行しクッキーに格納
- PostgreSQL + SQLAlchemy Async を用いたユーザー / 連携アカウントの永続化
- DI コンテナによるコンテキスト分離（UsersContext）の実装
- Alembic によるマイグレーション管理、`uv` ベースの依存管理、Docker 対応

## 技術スタック
- Python 3.12 / FastAPI / Uvicorn
- Authlib による Auth0 連携、PyJWT による内部トークン発行
- SQLAlchemy Async + asyncpg / Alembic
- Docker Compose,  `uv` package manager

## ディレクトリ構成（抜粋）
```
├─ src/
│  ├─ main.py                # FastAPI アプリエントリポイント
│  ├─ cli.py                 # `uv run up` で利用する CLI エントリ
│  ├─ config.py              # Pydantic Settings による設定
│  ├─ infrastructure/        # DB 接続や DI コンテナ
│  └─ authproviderconnector/
│       └─ context/users/    # 認証ドメイン（ドメイン/アプリケーション/インフラ層）
├─ alembic/                  # マイグレーションスクリプト
├─ compose.yaml              # Docker Compose 定義
├─ Makefile                  # 開発用ヘルパーコマンド
```

### Docker Compose で起動
1. 依存関係（uv 仮想環境を含む）は Docker イメージ内でビルド時に解決されます。
2. 以下のコマンドで API + PostgreSQL を起動します。
   ```bash
   docker compose up --build
   ```
3. API は `http://localhost:8000` で待ち受け、ヘルスチェックは `http://localhost:8000/api/v1/health` です。OpenAPI ドキュメントは `http://localhost:8000/docs` で確認できます。

## データベースとマイグレーション
- データベースは PostgreSQL を前提とし、SQLAlchemy Async + asyncpg で接続します。
- 初期化後のテーブルは Alembic マイグレーションで管理します。
  ```bash
  make migrate          # 最新マイグレーションを適用
  make create-migrate m="add user table"  # 変更検出 → マイグレーション作成
  ```

## 品質チェック
- Lint: `make lint` (`ruff check .`)
- 自動整形: `make format` (`ruff --fix` + `ruff format`)

## API エンドポイント概要
| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/api/v1/health` | ヘルスチェック |
| GET | `/api/v1/auth/login` | Auth0（Google OAuth2）へのリダイレクトを返す |
| GET | `/api/v1/auth/callback` | 認証結果を受け取り内部アクセストークンとリフレッシュトークンを発行（クッキー設定） |
| POST | `/api/v1/auth/refresh` | リフレッシュトークンからトークンを再発行 |
| GET | `/api/v1/auth/me` | アクセストークンを検証しユーザー情報を返却 |
| GET | `/api/v1/auth/logout` | Auth0 ログアウト URL を返却 |
| GET | `/api/v1/auth/logout/callback` | クッキーを削除しクライアントへリダイレクト |

## 内部構成メモ
- `infrastructure/di.Container` がアプリ全体の依存をまとめ、HTTP リクエスト時に `UsersContext` を通じてユースケースを実行します。
- UsersContext は以下を束ねます。
  - `Auth0Client`: Auth0/OAuth2 連携、ID トークン検証
  - `PostgreSQLUserRepository`: ユーザー / 連携アカウントの永続化層
  - `Login/Callback/Refresh/Logout/GetAuthenticatedUser` 各ユースケース
- 内部 JWT は HS256 で署名され、アクセストークンは `Authorization: Bearer` で利用、リフレッシュトークンは HttpOnly クッキーとして保存されます。
- DB モデルは `users` と `linked_accounts` テーブルで構成され、Auth0 側のユーザー（sub）を `linked_accounts` として紐づけます。

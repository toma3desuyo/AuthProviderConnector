# 認証フロー

## Google OAuth と Auth0 の統合

```mermaid
sequenceDiagram
    participant Client as Client (Browser)
    participant FastAPI as FastAPI Server
    participant Auth0 as Auth0

    Note over Client,Auth0: Login Flow

    Client->>FastAPI: GET /login
    FastAPI->>FastAPI: Generate nonce (replay attack protection)
    FastAPI->>FastAPI: Generate state (CSRF protection)
    FastAPI->>FastAPI: Encrypt nonce & state
    FastAPI->>Client: Set encrypted cookie
    FastAPI->>Client: Redirect to Auth0 login page

    Client->>Auth0: Access Auth0 login page
    Auth0->>Auth0: User authenticates with Google
    Auth0->>Client: Redirect to /callback with authorization code

    Note over Client,Auth0: Callback Flow

    Client->>FastAPI: GET /callback?code=xxx&state=yyy
    FastAPI->>FastAPI: Verify state from cookie (CSRF check)
    FastAPI->>Auth0: Exchange authorization code for tokens
    Auth0->>FastAPI: Return Auth0 JWT & user info
    FastAPI->>FastAPI: Extract user info from Auth0 JWT
    FastAPI->>FastAPI: Create/update user in database
    FastAPI->>FastAPI: Generate application JWT
    FastAPI->>Client: Return application JWT

    Note over Client,FastAPI: Future API Calls

    Client->>FastAPI: API request with application JWT
    FastAPI->>FastAPI: Validate application JWT
    FastAPI->>Client: Return requested data
```

## 主要なセキュリティ機能

- **Nonce（ノンス）**: 各認証リクエストを一意にすることで、リプレイ攻撃を防止します
- **State（ステート）**: コールバックが元のリクエストと一致することを検証し、CSRF攻撃を防止します
- **Cookie暗号化**: 認証フロー中のnonceとstateの値を保護します
- **アプリケーションJWT**: Auth0のJWT形式からアプリを切り離し、将来的に認証プロバイダーを変更する際の柔軟性を提供します

## なぜAuth0のJWTではなくアプリケーションJWTを使用するのか？

1. **プロバイダー非依存性**: Auth0から他のプロバイダーに切り替えたり、追加の認証プロバイダーを導入する場合でも、クライアント側の変更が不要です
2. **カスタムクレーム**: Auth0の構造に依存せず、アプリケーション固有のクレームを追加できます
3. **トークン有効期限の制御**: 独自のトークン有効期限ポリシーを管理できます
4. **クライアントロジックの簡素化**: 認証方法に関係なく、クライアントは1つのJWT形式のみを理解すれば良くなります
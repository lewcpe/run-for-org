# Authentication Guide for Frontend Developers

The Run for Organization backend supports authentication via **OpenID Connect (OIDC)**. This allows integration with providers like **Auth0**, **Firebase**, **Okta**, or any compliant OIDC provider (e.g., Dex).

## Overview

1. **Frontend**: Authenticates the user with the Identity Provider (IdP).
2. **Frontend**: Receives an **Access Token** (or **ID Token**) from the IdP.
3. **Frontend**: Sends this token to the Backend in the `Authorization` header.
4. **Backend**: 
    - Verifies the OIDC token.
    - **Issues a new Internal JWT** signed by the backend.
5. **Frontend**: Uses the **Internal JWT** for all subsequent API requests.

## Authentication Header

All protected API endpoints require the following header:

```http
Authorization: Bearer <YOUR_INTERNAL_JWT>
```

## Supported Providers

### 1. Generic OIDC (Recommended)
Configure your frontend to use an OIDC-compliant library (e.g., `oidc-client-ts`, `react-oidc-context`, `next-auth`).

- **Issuer URL**: Must match `OIDC_ISSUER` in backend config.
- **Audience**: Must match `OIDC_AUDIENCE` in backend config.

- **Audience**: Must match `OIDC_AUDIENCE` in backend config.

### 2. OIDC via Backend Callback (Authorization Code Flow)
If you prefer the backend to handle the token exchange (e.g., to keep client secrets hidden):

1. **Frontend**: Redirects user to Provider's Authorization URL.
    - `client_id`: Your frontend client ID (if public) or Backend's client ID.
    - `redirect_uri`: `YOUR_BACKEND_URL/api/auth/callback`
    - `response_type`: `code`
    - `scope`: `openid profile email`
2. **Provider**: Redirects back to `YOUR_BACKEND_URL/api/auth/callback` with a `code`.
3. **Backend**: 
    - Exchanges the `code` for OIDC tokens.
    - Validates the OIDC Token.
    - Creates/Retrieves the User.
    - **Returns a new Internal JWT** (`access_token`).
    
**Endpoint**: `GET /api/auth/callback?code=...`

**Response**:
```json
{
  "access_token": "ey...",
  "token_type": "bearer",
  "user": { ... }
}
```

### 3. Auth0 / Firebase
Legacy support is available but Generic OIDC is preferred. If using Auth0 or Firebase SDKs, ensure the token sent to the backend is a valid JWT signed by the provider.

## User Claims

The backend relies on the **`email`** claim in the JWT to identify the user.
- Ensure your IdP includes the `email` claim in the token.
- If the user does not exist in the backend database, they will be **auto-created** upon their first successful authenticated request.

## Local Development with Dex

To test authentication locally without an external provider, we use **Dex**.

1. **Start Dex**:
   ```bash
   docker-compose up -d
   ```
   Dex will run at `http://127.0.0.1:5556/dex`.

2. **Frontend Configuration (Dev)**:
   - **Issuer**: `http://127.0.0.1:5556/dex`
   - **Client ID**: `example-app`
   - **Redirect URI**: `http://127.0.0.1:5555/callback` OR `http://127.0.0.1:8000/api/auth/callback` if using backend exchange.
   - **Scopes**: `openid profile email`

3. **Login Credentials (Dex)**:
   - **Email**: `admin@example.com`
   - **Password**: `password`

4. **Verify Token**:
   You can manually obtain a token from Dex (using a CLI or test app) and send it to the backend `GET /api/me` to verify.

## Configuration Endpoint

The frontend can discover OIDC settings (Issuer, Client ID) by calling:

```http
GET /api/config
```

Response:
```json
{
  "start_date": "2023-01-01",
  ...
  "oidc_issuer": "http://127.0.0.1:5556/dex",
  "oidc_client_id": "example-app",
  "oidc_callback_url": "http://127.0.0.1:8000/api/auth/callback",
  "oidc_login_url": "http://127.0.0.1:5556/dex/auth"
}
```

### `oidc_callback_url`
This field is populated by:
1. `OIDC_CALLBACK_URL` setting if configured.
2. Dynamically constructed from the current request (e.g., `https://api.example.com/api/auth/callback`) if not configured.

### `oidc_login_url`
This field is populated by:
1. `OIDC_AUTH_URL` setting if configured.
2. Dynamically discovered from `${OIDC_ISSUER}/.well-known/openid-configuration` if not configured.

The backend is configured via `.env` or environment variables:

- `OIDC_ISSUER`: The URL of the OIDC provider (e.g., `http://127.0.0.1:5556/dex` or `https://dev-xyz.us.auth0.com/`).
- `OIDC_AUDIENCE`: The expected audience claim (e.g., `run-for-org-app`).
- `OIDC_ALGORITHMS`: List of allowed algorithms (default `["RS256"]`).

## Troubleshooting

- **401 Unauthorized**:
    - Token is missing, expired, or invalid.
    - `iss` (Issuer) claim in token does not match `OIDC_ISSUER` env var.
    - `aud` (Audience) claim does not match `OIDC_AUDIENCE`.
    - `email` claim is missing.
- **Check Backend Logs**:
    - The backend logs authentication errors. Check the console output for `Auth error: ...`.

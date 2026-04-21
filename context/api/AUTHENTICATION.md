# Authentication

Production authentication using Supabase Auth with social sign-in.

---

## Overview

**Provider:** Supabase Auth
**Sign-in methods:** Apple Sign-In, Google Sign-In, Email/Password
**Token format:** JWT (verified locally by backend)

---

## Architecture

```
Flutter App → Supabase Auth (Apple/Google/Email) → JWT Token
                                                      ↓
FastAPI Backend ← Verify JWT locally (SUPABASE_JWT_SECRET)
       ↓
Map Supabase UUID → local student_id
```

**Key insight:** Backend verifies JWTs locally using Supabase's JWT secret. No round-trips to Supabase after initial auth.

---

## Supabase Configuration

### Project Details

| Setting | Value |
|---------|-------|
| **Project URL** | Set in environment: `SUPABASE_URL` |
| **Publishable Key** | Set in environment: `SUPABASE_ANON_KEY` |
| **JWT Secret** | Set in environment: `PAPERLAB_SUPABASE_JWT_SECRET` |

### Supabase Redirect URLs

All these must be added in Supabase Dashboard → Authentication → URL Configuration → Redirect URLs:

- `com.mypaperlab.paperlab://login-callback` (iOS/Android native)
- `http://localhost:8080/auth/callback` (web dev)
- `https://app.mypaperlab.com/auth/callback` (web production)

---

## Apple Sign-In Configuration

### Apple Developer Portal

| Setting | Value |
|---------|-------|
| **Bundle ID (iOS)** | `com.mypaperlab.paperlab` |
| **Services ID (Web)** | `com.mypaperlab.paperlab.service` |
| **Team ID** | Set in Apple Developer Portal |
| **Key ID** | Set in Apple Developer Portal |
| **Key File** | `AuthKey_<KEY_ID>.p8` (stored locally, not in repo) |

**Apple Developer Portal requirements:**
- App ID with Sign in with Apple capability
- Services ID linked to App ID with:
  - Domains: `yxapcpvkkpoqfasvujlw.supabase.co`, `localhost`, `app.mypaperlab.com`
  - Return URL: `https://yxapcpvkkpoqfasvujlw.supabase.co/auth/v1/callback`

### Supabase Apple Provider Settings

| Setting | Value |
|---------|-------|
| **Client ID** | `com.mypaperlab.paperlab,com.mypaperlab.paperlab.service` (comma-separated for both native + web) |
| **Secret Key** | JWT generated from .p8 file (see below) |

**IMPORTANT:** The secret key is NOT the raw .p8 file contents. It's a JWT you generate.

### Generating Apple Client Secret JWT

Run the script to generate the JWT:

```bash
uv run python scripts/generate_apple_secret.py /path/to/AuthKey.p8
```

Paste the output JWT into Supabase Apple provider "Secret Key" field.

**JWT expires every 6 months.** Set a calendar reminder.

- Current JWT generated: January 2026
- Next regeneration needed: July 2026

---

## Google Sign-In Configuration

### Google Cloud Console

| Setting | Value |
|---------|-------|
| **Project ID** | Set in Google Cloud Console |
| **Project Number** | Set in Google Cloud Console |

### OAuth Credentials

| Setting | Value |
|---------|-------|
| **Web Client ID** | Set in environment / Google Cloud Console |
| **Web Client Secret** | Set in environment / Google Cloud Console |
| **iOS Client ID** | Set in iOS build config |
| **iOS Reversed Client ID** | Reverse of iOS Client ID |

### Google Console Authorized URLs

**JavaScript Origins:**
- `http://localhost:8080`
- `https://yxapcpvkkpoqfasvujlw.supabase.co`
- `https://app.mypaperlab.com`

**Redirect URIs:**
- `https://yxapcpvkkpoqfasvujlw.supabase.co/auth/v1/callback`

### Supabase Google Provider Settings

| Setting | Value |
|---------|-------|
| **Client ID** | Web Client ID (above) |
| **Client Secret** | Web Client Secret (above) |
| **Skip nonce check** | **ENABLED** (required for native iOS to work) |

### Implementation

- **iOS Native:** Uses `google_sign_in` SDK with `signInWithIdToken`
- **Web:** Uses Supabase OAuth redirect flow

**iOS Info.plist requirements:**
- `GIDClientID`: iOS Client ID
- `CFBundleURLSchemes`: Reversed iOS Client ID

---

## Web OAuth Configuration

### Callback URLs

| Platform | Callback URL |
|----------|--------------|
| **iOS/Android (native)** | `com.mypaperlab.paperlab://login-callback` |
| **Web (localhost)** | `http://localhost:8080/auth/callback` |
| **Web (production)** | `https://app.mypaperlab.com/auth/callback` |

### Web OAuth Flow

```
User clicks Sign In → signInWithOAuth() → Redirect to Provider
                                              ↓
Provider authenticates → Redirect to Supabase callback
                                              ↓
Supabase exchanges code → Redirect to app /auth/callback
                                              ↓
Flutter router handles → Session established → Redirect to home
```

**Key file:** `lib/router.dart` - Contains `/auth/callback` route with `_AuthCallbackScreen`

---

## Web Deployment (Cloudflare Pages)

### URLs

| Environment | URL |
|-------------|-----|
| **Cloudflare Pages** | `https://paperlab-app.pages.dev` |
| **Custom Domain** | `https://app.mypaperlab.com` |

### Deployment

Deployed via GitHub Actions on push to `master` branch.

**Workflow:** `.github/workflows/deploy-web.yml`

Steps:
1. Checkout code
2. Setup Flutter 3.38.5
3. Get dependencies (`flutter pub get`)
4. Generate code (`dart run build_runner build --delete-conflicting-outputs`)
5. Build web (`flutter build web --release`)
6. Add SPA redirects (`_redirects` file)
7. Deploy to Cloudflare Pages via wrangler

**GitHub Secrets required:**
- `CLOUDFLARE_ACCOUNT_ID`
- `CLOUDFLARE_API_TOKEN`

### Backend CORS

**File:** `src/paperlab/api/main.py`

CORS allows:
- `http://localhost:*` (dev)
- `https://paperlab-app.pages.dev`
- `https://app.mypaperlab.com`

---

## Backend Implementation

### JWT Verification & Auto-Registration

**File:** `src/paperlab/api/auth.py`

```python
def get_current_student_id(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> int:
    # 1. Decode JWT with SUPABASE_JWT_SECRET, audience="authenticated"
    # 2. Extract supabase_uid from 'sub' claim
    # 3. Get or create student_id by supabase_uid (auto-registration)
```

**Auto-creation pattern:** Students are auto-created on first authenticated API request.

---

## Flutter Implementation

### Dependencies

```yaml
supabase_flutter: ^2.12.0
sign_in_with_apple: ^6.1.0
google_sign_in: ^6.2.0
crypto: ^3.0.0
```

### Auth Service

**File:** `lib/services/auth_service.dart`

Singleton pattern: `AuthService.instance`

**Methods:**
- `signInWithApple()` - Native on iOS, OAuth redirect on web
- `signInWithGoogle()` - Native on iOS, OAuth redirect on web
- `signInWithPassword(email, password)` - Email/password
- `signOut()` - Clear session
- `accessToken` - Get current JWT for API calls

### Deep Links

**iOS:** `ios/Runner/Info.plist`
```xml
<key>CFBundleURLSchemes</key>
<array>
  <string>com.mypaperlab.paperlab</string>
</array>
```

---

## Environment Variables

### Railway (Backend)

```
PAPERLAB_SUPABASE_JWT_SECRET=<your-jwt-secret>
```

### Flutter (Build-time)

Defaults are set in `lib/config.dart` so these are optional:
```
--dart-define=SUPABASE_URL=<your-supabase-url>
--dart-define=SUPABASE_ANON_KEY=<your-anon-key>
```

---

## Key Rotation Schedule

### Apple Client Secret JWT

Generated from `.p8` key file. Expires every 6 months.

- **Script:** `scripts/generate_apple_secret.py`
- **Current JWT generated:** January 2026
- **Next regeneration:** July 2026

### Apple Signing Key (.p8)

The `.p8` key itself doesn't expire, but Apple recommends rotation.

- **Key file:** `AuthKey_<KEY_ID>.p8`
- **Location:** Stored locally, not in repo

---

## Troubleshooting

### Apple: "missing OAuth secret"
- Supabase Apple provider not configured for web
- Need to add the JWT secret (not raw .p8 contents)

### Apple: "unacceptable audience"
- Client ID in Supabase must include BOTH bundle ID and Services ID
- Use comma-separated: `com.mypaperlab.paperlab,com.mypaperlab.paperlab.service`

### Google: "nonce" errors on iOS
- Enable "Skip nonce check" in Supabase Google provider settings

### Google: Redirects to localhost on production
- Check `app.mypaperlab.com/auth/callback` is in Supabase redirect URLs
- Check CORS includes the production domain

### Web: Blank page after deploy
- Check browser console for errors
- Verify `_redirects` file exists in build output
- Check Cloudflare Pages deployment includes files

---

## Related Documentation

- `context/frontend/ARCHITECTURE.md` → Flutter patterns
- `context/backend/ARCHITECTURE.md` → Backend patterns

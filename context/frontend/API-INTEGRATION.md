# API Integration

HTTP client patterns for calling backend APIs from Flutter.

---

## Repository Layer Pattern

**Architecture:**
```
Screen → Provider → Repository → ApiClient → DioClient → Backend API
                                                ↓
                                         Error Interceptor
```

**Purpose:** Separate API calls from state management. Providers orchestrate, repositories execute.

---

## HTTP Client Architecture

**Uses Dio with global error interceptor (not http package).**

**Why Dio:**
- Global interceptors for error handling
- Better timeout management
- Industry standard (130k+ pub.dev likes)
- Type-safe response handling

**See `ARCHITECTURE.md` for migration rationale.**

---

## DioClient Pattern

**Centralized Dio instance with global error interceptor.**

**Responsibilities:**
- Inject auth headers on all requests (except R2 presigned URLs)
- Convert all DioException → NetworkException types
- Handle connection errors, timeouts, API errors automatically

**Error flow:**
```
Network failure → DioException → Interceptor → NetworkException → Repository
```

**Where:** See `lib/services/dio_client.dart`

---

## ApiClient Pattern

**Thin wrapper around DioClient for repository use.**

**Responsibilities:**
- Extract response data from Dio responses
- Extract NetworkException from DioException.error
- Provide parseJson() helper for repositories

**Benefits:**
- Repositories don't depend on Dio directly
- Clean interface for HTTP operations
- Consistent error propagation

**Where:** See `lib/repositories/api_client.dart`

---

## Repository Pattern

**One repository per domain resource.**

**Responsibilities:**
- Map endpoints to typed functions
- Parse JSON to domain models (via fromJson)
- Let NetworkException propagate to providers

**Where:** See `lib/repositories/attempts_repository.dart` for pattern

### Discovery Repository

**Purpose:** Fetch available papers and questions for selection screens.

**Endpoints:**
- `GET /api/papers` - List all papers (with optional filters)
- `GET /api/questions` - List all questions (with optional filters)

**Where:** See `lib/repositories/discovery_repository.dart`

### Upload Repository

**Purpose:** Handle presigned URLs, R2 uploads, and submission operations.

**Endpoints:**
- `POST /api/uploads/presigned-url` - Get presigned URL for R2 upload
- `POST /api/attempts/papers` - Create draft paper attempt
- `POST /api/attempts/papers/{id}/questions` - Submit one question
- `POST /api/attempts/papers/{id}/submit` - Finalize paper
- `POST /api/attempts/questions` - Single-phase practice submission

**Cross-platform uploads:** Uses `XFile` from image_picker for web/mobile/desktop compatibility.

**Where:** See `lib/repositories/upload_repository.dart`

---

## Exception Hierarchy

**All network errors are NetworkException subtypes:**

```dart
sealed class NetworkException {
  NoConnectivityException    // No WiFi/cellular
  RequestTimeoutException     // Request timeout
  ApiException                // 4xx/5xx from server
  UploadException            // Upload-specific failures
  UnknownNetworkException    // Unexpected errors
}
```

**Why sealed:** Type-safe exhaustive pattern matching in catch blocks.

**Error sources:**
- `NoConnectivityException` → SocketException, connection errors
- `RequestTimeoutException` → Dio timeout exceeded
- `ApiException` → HTTP 4xx/5xx responses (includes statusCode)
- `UploadException` → R2 upload or presigned URL failures
- `UnknownNetworkException` → Catch-all for unexpected cases

**Where:** See `lib/exceptions/network_exceptions.dart`

---

## Provider Error Handling

**Catch specific exception types for type safety:**
- `ApiException` → Handle based on status code (401 = navigate to login)
- `NoConnectivityException` → Show "no internet" message
- `NetworkException` → Show generic error

**Best practice:** Don't show raw exception text to users. Use `ErrorMessages.getUserMessage(e)` for user-friendly messages.

**Where:** See `lib/providers/attempts_provider.dart` for pattern

**See `STATE-MANAGEMENT.md` for UI error handling patterns.**

**See `DESIGN_SYSTEM.md` for error messaging standards.**

---

## Cross-Platform File Handling

### Uploading Files (XFile Pattern)

**Problem:** File uploads work differently on web (bytes) vs mobile/desktop (File objects).

**Solution:** Use `XFile` from image_picker package for platform-agnostic file handling.

**Why XFile:**
- Works on web, mobile, and desktop
- Consistent API across platforms
- Integrates with image_picker for camera/gallery selection

**Pattern:** Read bytes with `file.readAsBytes()`, then HTTP PUT with bytes to presigned URL.

**Where:** See `lib/repositories/upload_repository.dart:uploadToR2()`

### Displaying Presigned URLs (CachedNetworkImage Pattern)

**Problem:** Results screens display student work images from R2 using presigned URLs (not local files).

**Solution:** Use `cached_network_image` package for network image display with caching.

**Why CachedNetworkImage:**
- Automatic caching (avoid re-downloading same image)
- Built-in loading/error states
- Memory and disk cache management
- Works across all platforms (web, mobile, desktop)

**Presigned URL expiry:** URLs expire after 1 hour (backend default). If user keeps results screen open past expiry, error widget displays. User can navigate back and return to get fresh URLs.

**Where:** See `lib/screens/question_results_screen.dart`, `lib/models/question_detail_result.dart`

**See:** `backend/STORAGE.md` → Presigned URL Security for backend URL generation pattern.

---

## OAuth2 Body Format

**Token endpoint requires URL-encoded body (not JSON).**

**Why:** FastAPI's OAuth2PasswordRequestForm expects URL-encoded format per OAuth2 spec.

**Pattern:** URL-encode email/password, set `Content-Type: application/x-www-form-urlencoded`.

**Where:** See `lib/services/auth_service.dart:login()`

---

## Singleton Providers

**Use Riverpod for dependency injection.**

**Pattern:** `@Riverpod(keepAlive: true)` for DioClient and ApiClient providers.

**Why:** Single instance shared across all repositories. Lifecycle managed by Riverpod.

**Where:** See `lib/providers/providers.dart`

---

## Related Documentation

- `ARCHITECTURE.md` → HTTP client decision (http → Dio migration)
- `STATE-MANAGEMENT.md` → Error handling in providers and screens
- `DESIGN_SYSTEM.md` → User-friendly error messaging
- `WIDGETS.md` → Offline banner (global connectivity monitoring)
- `MODELS.md` → Model factories for JSON parsing

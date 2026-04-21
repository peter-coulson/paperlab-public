import 'package:paperlab/repositories/api_client.dart';

/// Repository for account-related API operations.
///
/// Handles:
/// - Account deletion (deletes all user data from backend)
class AccountRepository {
  AccountRepository({required this.client});

  final ApiClient client;

  /// DELETE /api/account
  ///
  /// Permanently deletes the user's account and all associated data.
  /// This is a destructive operation that cannot be undone.
  ///
  /// ## Backend Implementation Requirements
  ///
  /// The backend MUST perform the following in order:
  ///
  /// 1. **Delete Supabase Auth User** (do this FIRST)
  ///    ```python
  ///    supabase.auth.admin.delete_user(user_id)
  ///    ```
  ///    This requires the `service_role` key (never expose client-side).
  ///    Doing this first ensures the user can't re-authenticate if later
  ///    steps fail.
  ///
  /// 2. **Delete User Data from Database**
  ///    - All paper attempts and results
  ///    - All question attempts and results
  ///    - Use cascade deletes where possible
  ///
  /// 3. **Delete Images from R2 Storage**
  ///    - All uploaded exam paper images
  ///
  /// ## Apple App Store Compliance
  ///
  /// This endpoint is required for Apple App Store compliance (Guideline
  /// 5.1.1(v)). The account deletion must be complete - users must not be
  /// able to log back in after deletion.
  ///
  /// ## Error Handling
  ///
  /// If any step fails, the backend should:
  /// - Return an appropriate error status
  /// - Log the failure for manual cleanup if needed
  /// - The auth user deletion (step 1) should be prioritized since partial
  ///   deletion with data remaining is preferable to a deleted-data user
  ///   who can still authenticate
  Future<void> deleteAccount() async {
    await client.delete('/api/account');
  }
}

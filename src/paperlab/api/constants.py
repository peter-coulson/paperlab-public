"""API layer constants.

Centralized definitions for error messages, timeouts, and other magic values.
"""

# HTTP Error Messages
ERROR_ATTEMPT_NOT_FOUND = "Attempt not found"
ERROR_ALREADY_SUBMITTED = "Already submitted"
ERROR_PAPER_ALREADY_SUBMITTED = "Paper already submitted"
ERROR_NOT_A_DRAFT = "Paper already submitted (not a draft)"
ERROR_QUESTION_NOT_FOUND = "Question not found"
ERROR_INVALID_STAGING_KEY = "Invalid staging key"

# Presigned URL Configuration
PRESIGNED_URL_EXPIRY_SECONDS = 3600  # 1 hour

# Status String Literals (matches Literal types in models/status.py)
STATUS_DRAFT = "draft"
STATUS_SUBMITTED = "submitted"
STATUS_MARKING = "marking"
STATUS_READY_FOR_GRADING = "ready_for_grading"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

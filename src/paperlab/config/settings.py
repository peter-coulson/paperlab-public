"""Runtime settings with environment variable support.

This module contains the Settings class which manages all runtime configuration
including environment variables, paths, and computed properties.

All configuration should be accessed through the singleton `settings` instance.
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Import constants needed by Settings
# Note: Importing from same package to avoid circular imports
from paperlab.config.constants import LLMProviders


class Settings(BaseSettings):  # type: ignore[misc]
    """Application settings with environment variable support.

    Configuration can be set via:
    1. Environment variables (prefix: PAPERLAB_)
    2. .env file in project root
    3. Defaults defined here

    Example environment variables:
        PAPERLAB_DATABASE_NAME=marking.db
        PAPERLAB_SAMPLE_DATA_ENABLED=true
        PAPERLAB_ANTHROPIC_API_KEY=sk-ant-...
    """

    # ========================================================================
    # Database Configuration
    # ========================================================================
    database_name: str = "marking.db"
    database_path: Path | None = None  # Auto-computed from database_name if None
    schema_file: str = "schema.sql"
    evaluation_database_name: str = "evaluation_results.db"
    evaluation_schema_file: str = "evaluation_results_schema.sql"

    # ========================================================================
    # LLM API Configuration
    # ========================================================================

    # API Keys (loaded from environment variables - never commit these!)
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # LLM configuration
    # Set via PAPERLAB_DEFAULT_MODEL env var for production use
    default_model: str = ""
    max_prompt_tokens: int = 100_000

    # Provider-specific settings
    llm_timeout: int = 120  # Seconds
    llm_max_retries: int = 3
    llm_temperature: float = 0.3  # Low temperature for consistent marking
    llm_max_tokens: int = 4096  # Maximum tokens in response

    # Batch marking configuration (provider-specific)
    # Controls parallel workers for BatchMarker - tune based on API tier
    #
    # Anthropic Claude defaults:
    #   - Tier 1 (default): 50 req/min  → 5 workers = ~10 req/min (20% utilization)
    #   - Tier 2: 1000 req/min → 30 workers = ~60 req/min (safe)
    #   - Tier 3-4: 2000-4000 req/min → 60-80 workers = ~120-160 req/min (safe)
    batch_max_workers_anthropic: int = 5

    # OpenAI defaults:
    #   - Tier 1 (default): 30K TPM (tokens per min) → 5 workers = ~10K TPM (safe)
    #   - Higher tiers: Scale workers based on TPM limit (each request ~2K tokens)
    #   - Note: TPM limits are more restrictive than RPM for vision models
    batch_max_workers_openai: int = 5

    # Google Gemini defaults:
    #   - Free tier: 15 req/min → set to 2 workers manually
    #   - Pay-as-you-go: 2000 req/min → 200 workers = 20% utilization (safe)
    #   - Note: Gemini has generous rate limits, can scale much higher than Anthropic
    batch_max_workers_google: int = 200

    # Deprecated: Use provider-specific settings above
    # Kept for backward compatibility, used as fallback for unknown providers
    batch_max_workers: int = 5

    # ========================================================================
    # Cloud Storage Configuration (Cloudflare R2)
    # ========================================================================

    # R2 credentials (loaded from environment variables - never commit these!)
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = ""  # Permanent storage
    r2_staging_bucket: str = ""  # Temporary staging (Flow 2)
    r2_public_url: str = ""  # Public r2.dev URL (e.g., https://pub-{hash}.r2.dev)

    # ========================================================================
    # Supabase Authentication Configuration
    # ========================================================================

    # Supabase JWT secret for token verification (from Settings > API > JWT Secret)
    # Required for verifying Supabase-issued JWTs in the backend
    supabase_jwt_secret: str = ""

    # Supabase project URL (e.g., https://your-project.supabase.co)
    # Only needed if backend makes direct Supabase API calls (not typical)
    supabase_url: str = ""

    # Supabase service role key (from Settings > API > Service Role Key)
    # Required for admin operations like deleting users
    # WARNING: This key has full access - never expose client-side
    supabase_service_role_key: str = ""

    # ========================================================================
    # Base Directories
    # ========================================================================
    data_dir: str = "data"
    db_dir: str = "data/db"
    prompts_dir: str = "prompts"

    # ========================================================================
    # Production Data Paths (marking.db content)
    # ========================================================================

    # Configuration JSONs (reference data for production DB)
    config_dir: str = "data/config"

    # Paper Content
    papers_dir: str = "data/papers"
    papers_sources_dir: str = "data/papers/sources"
    papers_structured_dir: str = "data/papers/structured"
    papers_diagrams_dir: str = "data/papers/diagrams"

    # Student Work
    students_dir: str = "data/students"
    students_work_dir: str = "data/students/work"

    # ========================================================================
    # Evaluation Data Paths (evaluation_results.db content)
    # ========================================================================

    evaluation_dir: str = "data/evaluation"
    evaluation_config_dir: str = "data/evaluation/config"
    evaluation_test_cases_dir: str = "data/evaluation/test_cases"
    evaluation_test_suites_dir: str = "data/evaluation/test_suites"

    # ========================================================================
    # Export Paths (generated outputs)
    # ========================================================================

    exports_dir: str = "data/exports"
    exports_markdown_dir: str = "data/exports/markdown"
    exports_reports_dir: str = "data/exports/reports"

    # ========================================================================
    # Application Settings
    # ========================================================================

    # Environment
    environment: str = "development"  # development, staging, production

    # Formatting defaults
    markdown_base_heading_level: int = 2

    # Sample data configuration (for testing)
    sample_data_enabled: bool = True
    sample_data_config: str = "data/config/sample_data.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="PAPERLAB_",
        extra="ignore",  # Ignore extra environment variables
    )

    # Validators for API keys (format checking only - don't require keys at startup)
    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str) -> str:
        """Validate Anthropic API key format if provided."""
        if v and not v.startswith("sk-ant-"):
            raise ValueError(
                "Anthropic API key must start with 'sk-ant-'. "
                "Get your key at: https://console.anthropic.com/"
            )
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key format if provided."""
        if v and not v.startswith("sk-"):
            raise ValueError(
                "OpenAI API key must start with 'sk-'. "
                "Get your key at: https://platform.openai.com/api-keys"
            )
        return v

    @field_validator("google_api_key")
    @classmethod
    def validate_google_key(cls, v: str) -> str:
        """Validate Google API key format if provided."""
        if v and not v.startswith("AI"):
            raise ValueError(
                "Google API key must start with 'AI'. "
                "Get your key at: https://aistudio.google.com/apikey"
            )
        return v

    @field_validator("max_prompt_tokens")
    @classmethod
    def validate_token_limit(cls, v: int) -> int:
        """Validate token limit is reasonable."""
        if v < 1000 or v > 200_000:
            raise ValueError("max_prompt_tokens must be between 1,000 and 200,000")
        return v

    @field_validator("llm_timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Validate timeout is reasonable."""
        if v < 10 or v > 600:
            raise ValueError("llm_timeout must be between 10 and 600 seconds")
        return v

    @field_validator("llm_max_retries")
    @classmethod
    def validate_max_retries(cls, v: int) -> int:
        """Validate max retries is reasonable."""
        if v < 0 or v > 10:
            raise ValueError("llm_max_retries must be between 0 and 10")
        return v

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if v < 0.0 or v > 1.0:
            raise ValueError("llm_temperature must be between 0.0 and 1.0")
        return v

    @field_validator("llm_max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        """Validate max tokens is reasonable."""
        if v < 100 or v > 16_384:
            raise ValueError("llm_max_tokens must be between 100 and 16,384")
        return v

    @field_validator("batch_max_workers")
    @classmethod
    def validate_batch_max_workers(cls, v: int) -> int:
        """Validate batch max workers is reasonable."""
        if v < 1 or v > 100:
            raise ValueError("batch_max_workers must be between 1 and 100")
        return v

    @field_validator("batch_max_workers_anthropic")
    @classmethod
    def validate_batch_max_workers_anthropic(cls, v: int) -> int:
        """Validate Anthropic batch max workers is reasonable."""
        if v < 1 or v > 100:
            raise ValueError("batch_max_workers_anthropic must be between 1 and 100")
        return v

    @field_validator("batch_max_workers_openai")
    @classmethod
    def validate_batch_max_workers_openai(cls, v: int) -> int:
        """Validate OpenAI batch max workers is reasonable."""
        if v < 1 or v > 1000:
            raise ValueError("batch_max_workers_openai must be between 1 and 1000")
        return v

    @field_validator("batch_max_workers_google")
    @classmethod
    def validate_batch_max_workers_google(cls, v: int) -> int:
        """Validate Google batch max workers is reasonable."""
        if v < 1 or v > 1000:
            raise ValueError("batch_max_workers_google must be between 1 and 1000")
        return v

    @property
    def project_root(self) -> Path:
        """Get project root directory.

        File location: src/paperlab/config/settings.py
        Navigation: settings.py → config/ → paperlab/ → src/ → project_root/
        (Requires 4 .parent calls: file to directory, then 3 directory levels up)
        """
        return Path(__file__).parent.parent.parent.parent

    # ========================================================================
    # Computed Path Properties - Database
    # ========================================================================

    @property
    def db_path(self) -> Path:
        """Get full database path.

        Returns custom path if database_path is set,
        otherwise returns data/db/database_name
        """
        if self.database_path:
            return self.database_path
        return self.project_root / self.db_dir / self.database_name

    @property
    def schema_path(self) -> Path:
        """Get full production schema file path."""
        return self.project_root / self.db_dir / self.schema_file

    @property
    def evaluation_db_path(self) -> Path:
        """Get full evaluation database path."""
        return self.project_root / self.db_dir / self.evaluation_database_name

    @property
    def evaluation_schema_path(self) -> Path:
        """Get full evaluation schema file path."""
        return self.project_root / self.db_dir / self.evaluation_schema_file

    # ========================================================================
    # Computed Path Properties - Production Data
    # ========================================================================

    @property
    def config_path(self) -> Path:
        """Get full path to config directory (exam configs, LLM models)."""
        return self.project_root / self.config_dir

    @property
    def papers_path(self) -> Path:
        """Get full path to papers base directory."""
        return self.project_root / self.papers_dir

    @property
    def papers_sources_path(self) -> Path:
        """Get full path to paper sources directory (PDFs)."""
        return self.project_root / self.papers_sources_dir

    @property
    def papers_structured_path(self) -> Path:
        """Get full path to structured papers directory (JSONs)."""
        return self.project_root / self.papers_structured_dir

    @property
    def papers_diagrams_path(self) -> Path:
        """Get full path to papers diagrams directory."""
        return self.project_root / self.papers_diagrams_dir

    @property
    def students_path(self) -> Path:
        """Get full path to students base directory."""
        return self.project_root / self.students_dir

    @property
    def students_work_path(self) -> Path:
        """Get full path to student work directory."""
        return self.project_root / self.students_work_dir

    # ========================================================================
    # Computed Path Properties - Evaluation Data
    # ========================================================================

    @property
    def evaluation_path(self) -> Path:
        """Get full path to evaluation base directory."""
        return self.project_root / self.evaluation_dir

    @property
    def evaluation_config_path(self) -> Path:
        """Get full path to evaluation config directory (validation_types.json)."""
        return self.project_root / self.evaluation_config_dir

    @property
    def evaluation_test_cases_path(self) -> Path:
        """Get full path to test cases directory."""
        return self.project_root / self.evaluation_test_cases_dir

    @property
    def evaluation_test_suites_path(self) -> Path:
        """Get full path to test suites directory."""
        return self.project_root / self.evaluation_test_suites_dir

    # ========================================================================
    # Computed Path Properties - Exports
    # ========================================================================

    @property
    def exports_path(self) -> Path:
        """Get full path to exports base directory."""
        return self.project_root / self.exports_dir

    @property
    def exports_markdown_path(self) -> Path:
        """Get full path to markdown exports directory."""
        return self.project_root / self.exports_markdown_dir

    @property
    def exports_reports_path(self) -> Path:
        """Get full path to reports exports directory."""
        return self.project_root / self.exports_reports_dir

    # ========================================================================
    # Computed Path Properties - Prompts
    # ========================================================================

    @property
    def prompts_path(self) -> Path:
        """Get full path to prompts directory."""
        return self.project_root / self.prompts_dir

    # ========================================================================
    # Computed Path Properties - Other
    # ========================================================================

    @property
    def sample_config_path(self) -> Path:
        """Get full path to sample data configuration."""
        return self.project_root / self.sample_data_config

    # ========================================================================
    # Environment Properties
    # ========================================================================

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    def get_api_key_for_provider(self, provider: str) -> str:
        """Get API key for LLM provider.

        Args:
            provider: Provider name (use LLMProviders constants)

        Returns:
            API key for the provider

        Raises:
            ValueError: If provider unknown or API key not configured

        Security:
            - Keys loaded from environment variables only
            - Never hardcoded or committed to repo
            - Validated at access time (fail fast)

        Example:
            >>> settings.get_api_key_for_provider(LLMProviders.ANTHROPIC)
            "sk-ant-..."  # From PAPERLAB_ANTHROPIC_API_KEY env var

            >>> settings.get_api_key_for_provider("unknown")
            ValueError: Unknown provider: unknown
        """
        # Map provider to corresponding API key field
        # Uses LLMProviders constants to ensure consistency
        key_map = {
            LLMProviders.ANTHROPIC: (self.anthropic_api_key, "ANTHROPIC_API_KEY"),
            LLMProviders.OPENAI: (self.openai_api_key, "OPENAI_API_KEY"),
            LLMProviders.GOOGLE: (self.google_api_key, "GOOGLE_API_KEY"),
        }

        if provider not in key_map:
            raise ValueError(
                f"Unknown provider: {provider}\n"
                f"Supported providers: {', '.join(LLMProviders.all())}"
            )

        api_key, env_var_name = key_map[provider]

        if not api_key:
            raise ValueError(
                f"No API key configured for {provider}\n"
                f"Set environment variable: PAPERLAB_{env_var_name}\n"
                f"Or add to .env file: PAPERLAB_{env_var_name}=your-key-here\n"
                f"See .env.example for details"
            )

        return api_key


# Global settings instance
# Import this in other modules: from paperlab.config import settings
settings = Settings()

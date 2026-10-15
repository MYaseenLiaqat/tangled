import logging
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/tangled.db"
    env: str = "dev"
    jwt_secret: str = "change-me"
    chroma_dir: str = "./data/chroma"
    embedding_cache_dir: str = "./data/embedding-cache"
    upload_dir: str = "./data/uploads"
    llm_api_key: str = ""
    llm_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    llm_timeout: float = 30.0
    llm_max_retries: int = 1
    min_similarity: float = 0.25
    rag_top_k: int = 4
    llm_json_mode: Literal["auto", "on", "off"] = "auto"
    llm_max_concurrency: int = 4
    analysis_max_retries: int = 3
    max_evidence_phrase_chars: int = 120
    max_quiz_import_mb: int = 5
    intent_backend: str = "llm"    # llm | logreg
    intent_model_path: str = "./data/intent.joblib"
    min_conf: float = 0.70
    min_students: int = 4
    quiz_low: float = 0.60
    max_upload_mb: int = 25
    rate_limit_per_min: int = 30
    max_chat_input_chars: int = 1000
    max_llm_output_tokens: int = 500
    consent_version: str = "2026-10-14"
    enrolled: int = 24
    cors_origins: str = "http://localhost:5173"
    request_max_bytes: int = 2_000_000
    trusted_proxy: str = ""
    join_rate_limit_per_min: int = 100
    chat_ip_rate_limit_per_min: int = 120
    chat_student_rate_limit_per_min: int = 60
    login_rate_limit_per_min: int = 10

    def validate_runtime(self) -> None:
        if self.env not in ("dev", "prod"):
            raise ValueError("ENV must be dev or prod")
        errors = []
        if self.jwt_secret == "change-me" or len(self.jwt_secret) < 32:
            errors.append("JWT_SECRET must be at least 32 characters and not use the default")
        if not self.llm_api_key:
            errors.append("LLM_API_KEY must be set")
        if "*" in {origin.strip() for origin in self.cors_origins.split(",")}:
            errors.append("CORS_ORIGINS must not contain a wildcard")
        if errors and self.env == "prod":
            raise ValueError("; ".join(errors))
        for error in errors:
            logging.getLogger("tangled.config").warning("development safety check: %s", error)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_proxy_list(self) -> list[str]:
        return [proxy.strip() for proxy in self.trusted_proxy.split(",") if proxy.strip()]


settings = Settings()

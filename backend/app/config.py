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

    def validate_runtime(self) -> None:
        if self.env not in ("dev", "prod"):
            raise ValueError("ENV must be dev or prod")
        if self.env == "prod" and self.jwt_secret == "change-me":
            raise ValueError("JWT_SECRET must be set in prod")


settings = Settings()

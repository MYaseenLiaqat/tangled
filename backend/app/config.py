from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///./data/tangled.db"
    chroma_dir: str = "./data/chroma"
    upload_dir: str = "./data/uploads"
    teacher_token: str = "change-me"
    llm_api_key: str = ""
    llm_base_url: str | None = None
    llm_model: str = "gpt-4o-mini"
    min_similarity: float = 0.30   # below this the tutor refuses; no LLM call is made
    intent_backend: str = "llm"    # llm | logreg
    intent_model_path: str = "./data/intent.joblib"
    min_conf: float = 0.70         # minimum classifier confidence to count a message as confusion
    min_students: int = 4          # distinct students required before a topic is flagged
    quiz_low: float = 0.60         # quiz correct-rate below this counts as corroboration
    enrolled: int = 24


settings = Settings()

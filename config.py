from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    gemini_api_key: str = ""
    whisper_mode: str = "local"       # "local" or "api"
    whisper_model_size: str = "small"  # tiny, base, small, medium, large

    class Config:
        env_file = ".env"


settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://podlistener:podlistener@postgres:5432/podlistener"
    DATABASE_URL_SYNC: str = "postgresql://podlistener:podlistener@postgres:5432/podlistener"
    REDIS_URL: str = "redis://redis:6379/0"
    WHISPER_API_URL: str = "http://whisper:8000"
    TRANSCRIPTION_PROVIDER: str = "local"
    TRANSCRIPTION_MODEL: str = "Systran/faster-whisper-small"
    CLOUD_TRANSCRIPTION_BASE_URL: str = "https://api.openai.com/v1"
    CLOUD_TRANSCRIPTION_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    LLM_PROVIDER: str = "ollama"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_SITE_URL: str = ""
    OPENROUTER_APP_NAME: str = "podlistener"
    AUDIO_DIR: str = "/data/audio"
    AUDIO_DOWNLOAD_TIMEOUT_SECONDS: int = 900
    AUDIO_DOWNLOAD_MAX_BYTES: int = 524288000
    TRANSCRIPTION_EXTERNAL_MAX_UPLOAD_BYTES: int = 26214400
    TRANSCRIPTION_EXTERNAL_CHUNK_SECONDS: int = 600
    TRANSCRIPTION_EXTERNAL_CHUNK_BITRATE_KBPS: int = 48
    TRANSCRIPTION_TIMEOUT_SECONDS: int = 900
    TRANSCRIPTION_TASK_RATE_LIMIT: str = "6/m"
    TRANSCRIPTION_429_RETRY_BASE_SECONDS: int = 90
    TRANSCRIPTION_429_RETRY_MAX_SECONDS: int = 1800
    PROCESS_EPISODE_SOFT_TIME_LIMIT_SECONDS: int = 1800
    PROCESS_EPISODE_TIME_LIMIT_SECONDS: int = 2100
    INITIAL_IMPORT_EPISODE_LIMIT: int = 10
    MAX_EPISODES_PER_FEED: int = 10

    model_config = {"env_file": ".env"}


settings = Settings()

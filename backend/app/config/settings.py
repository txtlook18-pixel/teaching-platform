from pydantic_settings import BaseSettings
from enum import Enum


class AIMode(str, Enum):
    API = "api"
    LOCAL = "local"


class AIProviderType(str, Enum):
    CLAUDE = "claude"
    OPENAI = "openai"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    # AI
    ai_mode: AIMode = AIMode.API
    ai_provider: AIProviderType = AIProviderType.OPENAI
    github_token: str = ""  # GITHUB_TOKEN для GitHub Models

    # Local AI
    local_model_name: str = "mistral:latest"
    local_base_url: str = "http://localhost:11434"
    local_timeout: int = 120

    # Database
    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/teaching_platform"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    jwt_secret: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 1440

    # Cache
    use_cache: bool = True
    cache_ttl: int = 3600

    # Email / SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

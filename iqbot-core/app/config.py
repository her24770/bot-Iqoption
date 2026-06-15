"""Configuración global cargada desde variables de entorno (.env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # IQ Option
    IQOPTION_EMAIL: str = ""
    IQOPTION_PASSWORD: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Base de datos
    DATABASE_URL: str = "postgresql://iqbot:password@iqbot-db:5432/iqbot_db"

    # Redis
    REDIS_URL: str = "redis://iqbot-redis:6379"

    # Auth dashboard
    JWT_SECRET: str = "cambia-esta-cadena"
    JWT_EXPIRE_HOURS: int = 24
    DASHBOARD_EMAIL: str = "admin@tudominio.com"
    DASHBOARD_PASSWORD: str = "admin"

    # App
    APP_ENV: str = "production"
    APP_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173"

    # Modelo ML
    MODEL_PATH: str = "model.pkl"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()

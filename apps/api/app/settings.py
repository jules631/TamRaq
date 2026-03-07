from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://tamarac:tamarac@localhost:5432/tamarac"
    AUTH0_DOMAIN: str = ""
    AUTH0_AUDIENCE: str = ""
    APP_ENCRYPTION_KEY: str = ""  # Fernet base64-encoded 32-byte key
    SSE_TOKEN_SIGNING_KEY: str = ""  # HMAC secret for SSE JWT
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

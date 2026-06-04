from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ValSync API"
    DATABASE_URL: str
    ALEMBIC_DATABASE_URL: str

    # CORS: allowed origins for frontend clients (local dev, portal and landing)
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://val-care-frontend.vercel.app",
        "https://69f3d9433982532a8ff5fbde--valsync.netlify.app",
    ]
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()  # pyright: ignore[reportCallIssue]
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Ecosistema Clínico API (ValSync & ValCare)"
    API_V1_STR: str = "/api/v1"
    
    # En el futuro aquí irá la URL de la base de datos real de Render o PostgreSQL local
    DATABASE_URL: str = "sqlite:///./valsync_valcare.db" 

    class Config:
        case_sensitive = True

settings = Settings()
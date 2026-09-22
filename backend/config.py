from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECTS_DIR: str    = "models/projets"
    SEUIL_DEFAULT: float = 0.5
    DEV_MODE: bool       = True

    # Clé API Google (pour scanner les dossiers Drive publics)
    GOOGLE_API_KEY: str  = ""

    # Auth (prod uniquement)
    SUPABASE_URL: str        = ""
    SUPABASE_ANON_KEY: str   = ""
    SUPABASE_JWT_SECRET: str = ""

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()

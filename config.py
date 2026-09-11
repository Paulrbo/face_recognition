from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Dossier des projets
    PROJECTS_DIR: str = "../models/projets"

    # Recherche
    SEUIL_DEFAULT: float = 0.5

    # Dev mode (désactive auth, sert les photos en local)
    DEV_MODE: bool = True

    # Supabase (pour la prod)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()

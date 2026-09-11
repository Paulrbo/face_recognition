from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Dossier où sont stockés les projets (relatif à la racine du repo)
    PROJECTS_DIR: str = "models/projets"

    # Seuil de distance cosine (0 = identique, 1 = opposé)
    SEUIL_DEFAULT: float = 0.5

    # Dev mode : désactive l'auth et sert les photos en local
    DEV_MODE: bool = True

    # Auth (prod uniquement)
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # CORS — domaines autorisés à appeler l'API
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
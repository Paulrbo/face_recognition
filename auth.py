from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if settings.DEV_MODE:
        return {"user_id": "dev", "email": "dev@local"}

    # TODO: brancher le vrai système d'auth en prod
    # Exemple avec Supabase JWT :
    # import jwt
    # token = credentials.credentials
    # payload = jwt.decode(token, settings.SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
    # return payload

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Auth non configurée en prod",
    )

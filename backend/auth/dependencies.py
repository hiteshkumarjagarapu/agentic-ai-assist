from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from auth.jwt_handler import verify_token
from auth.models import User
from database import get_db

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing token")
    if creds is None:
        raise unauthorized
    payload = verify_token(creds.credentials)
    if not payload:
        raise unauthorized
    user = db.get(User, payload.get("user_id"))
    if user is None:
        raise unauthorized
    return user

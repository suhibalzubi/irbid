from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db
from app.security import decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# existing login omitted here (kept in file)

@router.get('/me', response_model=schemas.UserOut)
def me(authorization: str = Header(None), db: Session = Depends(get_db)):
    """Return current user based on Authorization: Bearer <token> header."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid auth header')
    token = parts[1]
    payload = decode_access_token(token)
    if not payload or 'sub' not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
    user_id = int(payload['sub'])
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user

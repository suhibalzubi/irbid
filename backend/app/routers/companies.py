from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app import schemas, crud
from app.database import get_db
from app.security import decode_access_token

router = APIRouter(prefix="/companies", tags=["companies"])

# Simple dependency to get current user id from Authorization header (very small implementation)
from fastapi import Header

def get_current_user_id(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid auth header')
    token = parts[1]
    payload = decode_access_token(token)
    if not payload or 'sub' not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
    return int(payload['sub'])

@router.get('/', response_model=List[schemas.CompanyOut])
def list_companies(current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return crud.get_companies_for_owner(db, current_user_id)

@router.post('/', response_model=schemas.CompanyOut)
def create_company(company_in: schemas.CompanyCreate, current_user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    c = crud.create_company(db, owner_user_id=current_user_id, name=company_in.name, vat_number=company_in.vat_number, currency_code=company_in.currency_code, default_vat_rate=company_in.default_vat_rate)
    return c

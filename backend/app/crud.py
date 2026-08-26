from sqlalchemy.orm import Session
from app import models
from app.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, email: str, password: str, name: str = None):
    hashed = get_password_hash(password)
    user = models.User(email=email, password_hash=hashed, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Companies
def create_company(db: Session, owner_user_id: int, name: str, vat_number: str = None, currency_code: str = 'AED', default_vat_rate: float = 5.0):
    c = models.Company(owner_user_id=owner_user_id, name=name, vat_number=vat_number, currency_code=currency_code, default_vat_rate=default_vat_rate)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

def get_companies_for_owner(db: Session, owner_user_id: int):
    return db.query(models.Company).filter(models.Company.owner_user_id == owner_user_id).all()

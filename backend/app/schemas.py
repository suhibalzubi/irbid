from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str]

    class Config:
        orm_mode = True

# Company
class CompanyCreate(BaseModel):
    name: str
    vat_number: Optional[str] = None
    currency_code: Optional[str] = 'AED'
    default_vat_rate: Optional[float] = 5.0

class CompanyOut(BaseModel):
    id: int
    name: str
    vat_number: Optional[str]
    currency_code: str
    default_vat_rate: float

    class Config:
        orm_mode = True

# Invoice (minimal)
class InvoiceItemIn(BaseModel):
    product_id: Optional[int]
    description: str
    quantity: float
    unit_price: float
    tax_rate_id: Optional[int]

class InvoiceCreate(BaseModel):
    company_id: int
    type: str
    date: date
    due_date: Optional[date]
    customer_id: Optional[int]
    items: List[InvoiceItemIn]
    notes: Optional[str] = None

class InvoiceOut(BaseModel):
    id: int
    number: Optional[str]
    status: str

    class Config:
        orm_mode = True

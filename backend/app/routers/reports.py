from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from sqlalchemy import func
from datetime import datetime

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get('/trial-balance')
def trial_balance(company_id: int, date_to: str = None, db: Session = Depends(get_db)):
    q = db.query(models.JournalLine.account_code, func.coalesce(func.sum(models.JournalLine.debit),0).label('debit'), func.coalesce(func.sum(models.JournalLine.credit),0).label('credit'))
    q = q.join(models.JournalEntry, models.JournalEntry.id==models.JournalLine.journal_entry_id).filter(models.JournalEntry.company_id==company_id)
    if date_to:
        dt = datetime.fromisoformat(date_to).date()
        q = q.filter(models.JournalEntry.date <= dt)
    q = q.group_by(models.JournalLine.account_code)
    rows = q.all()
    result = [{'account_code': r[0], 'debit': float(r[1]), 'credit': float(r[2])} for r in rows]
    return {'data': result}

@router.get('/income-statement')
def income_statement(company_id: int, date_from: str = None, date_to: str = None, db: Session = Depends(get_db)):
    # Simple income statement: revenue (credit on SALES), expenses (debit on PURCHASES)
    q = db.query(models.JournalLine.account_code, func.coalesce(func.sum(models.JournalLine.credit),0).label('credit'), func.coalesce(func.sum(models.JournalLine.debit),0).label('debit'))
    q = q.join(models.JournalEntry, models.JournalEntry.id==models.JournalLine.journal_entry_id).filter(models.JournalEntry.company_id==company_id)
    if date_from:
        q = q.filter(models.JournalEntry.date >= datetime.fromisoformat(date_from).date())
    if date_to:
        q = q.filter(models.JournalEntry.date <= datetime.fromisoformat(date_to).date())
    q = q.group_by(models.JournalLine.account_code)
    rows = q.all()
    # classify by account code simple rules
    revenue = 0.0
    expenses = 0.0
    for r in rows:
        code = r[0]
        credit = float(r[1])
        debit = float(r[2])
        if str(code).startswith('4'):
            revenue += credit - debit
        elif str(code).startswith('5'):
            expenses += debit - credit
    return {'revenue': revenue, 'expenses': expenses, 'net_income': revenue - expenses}

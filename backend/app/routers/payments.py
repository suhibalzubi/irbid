from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from datetime import date
from decimal import Decimal

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post('/')
def create_payment(payment: dict, db: Session = Depends(get_db)):
    # Expected payment dict: {company_id, invoice_id (opt), payment_date, amount, method, reference}
    company_id = payment.get('company_id')
    invoice_id = payment.get('invoice_id')
    amount = Decimal(str(payment.get('amount')))
    pay_date = payment.get('payment_date') or date.today().isoformat()
    p = models.Payment(company_id=company_id, invoice_id=invoice_id, payment_date=pay_date, amount=amount, method=payment.get('method'), reference=payment.get('reference'))
    db.add(p)
    db.flush()
    # create journal entry
    je = models.JournalEntry(company_id=company_id, date=pay_date, ref_type='payment', ref_id=p.id, description=f'Payment {p.reference or ""}', total_debit=amount, total_credit=amount)
    db.add(je)
    db.flush()
    # For sales invoice: Debit Bank/Cash, Credit AR
    if invoice_id:
        inv = db.query(models.Invoice).filter(models.Invoice.id==invoice_id).first()
        if inv and inv.type == 'sales':
            line1 = models.JournalLine(journal_entry_id=je.id, account_code='1000', debit=amount, credit=0, description='Bank/Cash')
            line2 = models.JournalLine(journal_entry_id=je.id, account_code='1100', debit=0, credit=amount, description='Accounts Receivable')
            db.add_all([line1, line2])
            # update invoice status
            # sum payments
            total_paid = db.query(models.Payment).filter(models.Payment.invoice_id==invoice_id).with_entities(models.Payment.amount).all()
            paid_sum = sum([Decimal(str(x[0])) for x in total_paid]) if total_paid else Decimal('0')
            if paid_sum >= (inv.total or Decimal('0')):
                inv.status = 'paid'
            elif paid_sum > Decimal('0'):
                inv.status = 'partially_paid'
        else:
            # for purchase invoices: Debit AP, Credit Bank
            if inv and inv.type == 'purchase':
                line1 = models.JournalLine(journal_entry_id=je.id, account_code='2100', debit=amount, credit=0, description='Accounts Payable')
                line2 = models.JournalLine(journal_entry_id=je.id, account_code='1000', debit=0, credit=amount, description='Bank/Cash')
                db.add_all([line1, line2])
    db.commit()
    db.refresh(p)
    return {"status":"ok","payment_id":p.id}

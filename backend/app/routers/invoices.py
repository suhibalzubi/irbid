from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app import schemas
from app.database import get_db
from app import models
from decimal import Decimal
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
import os
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/invoices", tags=["invoices"])

# Helper account codes
AR = '1100'
SALES = '4000'
VAT_OUT = '2200'
AP = '2100'
PURCHASES = '5000'
VAT_IN = '2201'
BANK = '1000'

@router.post('/', response_model=schemas.InvoiceOut)
def create_invoice(invoice_in: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    inv = models.Invoice(
        company_id=invoice_in.company_id,
        type=invoice_in.type,
        date=invoice_in.date,
        due_date=invoice_in.due_date,
        customer_id=invoice_in.customer_id,
        status='draft'
    )
    db.add(inv)
    db.flush()  # get id
    subtotal = Decimal('0.00')
    tax_total = Decimal('0.00')
    for it in invoice_in.items:
        qty = Decimal(str(it.quantity))
        unit = Decimal(str(it.unit_price))
        line_sub = qty * unit
        tax_pct = None
        if it.tax_rate_id:
            tr = db.query(models.TaxRate).filter(models.TaxRate.id == it.tax_rate_id, models.TaxRate.company_id==invoice_in.company_id).first()
            if tr:
                tax_pct = Decimal(str(tr.rate_percent))
        else:
            comp = db.query(models.Company).filter(models.Company.id==invoice_in.company_id).first()
            tax_pct = Decimal(str(comp.default_vat_rate)) if comp else Decimal('0')
        line_tax = (line_sub * tax_pct / Decimal('100.00')) if tax_pct else Decimal('0.00')
        line_total = line_sub + line_tax
        ii = models.InvoiceItem(
            invoice_id=inv.id,
            product_id=it.product_id,
            description=it.description,
            quantity=qty,
            unit_price=unit,
            tax_rate_id=it.tax_rate_id,
            line_total=line_total
        )
        db.add(ii)
        subtotal += line_sub
        tax_total += line_tax
    inv.subtotal = subtotal
    inv.tax_total = tax_total
    inv.total = subtotal + tax_total
    db.commit()
    db.refresh(inv)
    return inv

@router.post('/{invoice_id}/issue')
def issue_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(models.Invoice).filter(models.Invoice.id==invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail='Invoice not found')
    if inv.status == 'issued':
        raise HTTPException(status_code=400, detail='Invoice already issued')
    # compute totals from items if not present
    items = db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id==inv.id).all()
    subtotal = sum((it.quantity * it.unit_price) for it in items)
    # compute tax properly by checking tax rates
    tax_total = Decimal('0.00')
    for it in items:
        if it.tax_rate_id:
            tr = db.query(models.TaxRate).filter(models.TaxRate.id==it.tax_rate_id).first()
            pct = Decimal(str(tr.rate_percent)) if tr else Decimal('0')
        else:
            comp = db.query(models.Company).filter(models.Company.id==inv.company_id).first()
            pct = Decimal(str(comp.default_vat_rate)) if comp else Decimal('0')
        line_sub = it.quantity * it.unit_price
        tax_total += (line_sub * pct / Decimal('100.00'))
    total = subtotal + tax_total
    # create journal entry
    je = models.JournalEntry(
        company_id=inv.company_id,
        date=inv.date,
        ref_type='invoice',
        ref_id=inv.id,
        description=f'Issue invoice {inv.number or "(unassigned)"}',
        total_debit=total,
        total_credit=total
    )
    db.add(je)
    db.flush()
    # depending on invoice type
    if inv.type == 'sales':
        # Debit AR (total), Credit Sales (subtotal), Credit VAT_OUT (tax_total)
        line1 = models.JournalLine(journal_entry_id=je.id, account_code=AR, debit=total, credit=0, description='Accounts Receivable')
        db.add(line1)
        line2 = models.JournalLine(journal_entry_id=je.id, account_code=SALES, debit=0, credit=subtotal, description='Sales Revenue')
        db.add(line2)
        if tax_total > 0:
            line3 = models.JournalLine(journal_entry_id=je.id, account_code=VAT_OUT, debit=0, credit=tax_total, description='VAT Output')
            db.add(line3)
    else:
        # purchase: Debit Purchases (subtotal), Debit VAT_IN (tax_total), Credit AP (total)
        line1 = models.JournalLine(journal_entry_id=je.id, account_code=PURCHASES, debit=subtotal, credit=0, description='Purchases')
        db.add(line1)
        if tax_total > 0:
            line2 = models.JournalLine(journal_entry_id=je.id, account_code=VAT_IN, debit=tax_total, credit=0, description='VAT Input')
            db.add(line2)
        line3 = models.JournalLine(journal_entry_id=je.id, account_code=AP, debit=0, credit=total, description='Accounts Payable')
        db.add(line3)
    inv.status = 'issued'
    # assign invoice number if missing
    if not inv.number:
        # simple generation: INV-YYYY-XXXX
        year = inv.date.year if inv.date else 2026
        # count existing invoices for company this year
        count = db.query(models.Invoice).filter(models.Invoice.company_id==inv.company_id, models.Invoice.number.like(f"INV-{year}-%")).count()
        seq = count + 1
        inv.number = f"INV-{year}-{seq:04d}"
    inv.subtotal = subtotal
    inv.tax_total = tax_total
    inv.total = total
    db.commit()
    return {"status":"ok", "invoice_id": inv.id}

@router.get('/{invoice_id}/pdf')
def invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(models.Invoice).filter(models.Invoice.id==invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail='Invoice not found')
    company = db.query(models.Company).filter(models.Company.id==inv.company_id).first()
    customer = db.query(models.Customer).filter(models.Customer.id==inv.customer_id).first() if inv.customer_id else None
    items = db.query(models.InvoiceItem).filter(models.InvoiceItem.invoice_id==inv.id).all()
    # prepare data for template
    inv_data = {
        'number': inv.number,
        'date': inv.date.isoformat() if inv.date else '',
        'subtotal': str(inv.subtotal or ''),
        'tax_total': str(inv.tax_total or ''),
        'total': str(inv.total or ''),
        'items': []
    }
    for it in items:
        # fetch tax pct
        pct = 0
        if it.tax_rate_id:
            tr = db.query(models.TaxRate).filter(models.TaxRate.id==it.tax_rate_id).first()
            pct = float(tr.rate_percent) if tr else 0
        inv_data['items'].append({'description': it.description, 'quantity': float(it.quantity), 'unit_price': float(it.unit_price), 'tax_percent': pct, 'line_total': float(it.line_total)})
    data = {'company': {'name': company.name if company else '' , 'address': '' , 'vat_number': company.vat_number if company else ''}, 'invoice': inv_data, 'customer': {'name': customer.name if customer else ''}}
    # render template
    env = Environment(loader=FileSystemLoader(searchpath=os.path.join(os.getcwd(),'docs')), autoescape=select_autoescape(['html','xml']))
    tpl = env.get_template('invoice_template.html')
    html_out = tpl.render(**data)
    # generate PDF
    pdf = HTML(string=html_out).write_pdf()
    return StreamingResponse(iter([pdf]), media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="invoice-{invoice_id}.pdf"'})

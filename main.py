import re
from dateutil.parser import parse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvoiceRequest(BaseModel):
    invoice_text: str


def first_match(patterns, text):
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def parse_amount(value):
    if value is None:
        return None

    value = re.sub(r"[^\d.,-]", "", value)
    value = value.replace(",", "")

    try:
        return float(value)
    except:
        return None


@app.get("/")
def home():
    return {"status": "running"}


@app.post("/extract")
def extract(req: InvoiceRequest):

    text = req.invoice_text

    invoice_no = first_match([
        r"Invoice\s*(?:No|Number)?\s*[:#]?\s*([A-Za-z0-9/\-]+)",
        r"Invoice\s*#\s*([A-Za-z0-9/\-]+)",
        r"Ref(?:erence)?\s*[:#]?\s*([A-Za-z0-9/\-]+)",
    ], text)

    vendor = first_match([
        r"Vendor\s*[:#]?\s*(.+)",
        r"Seller\s*[:#]?\s*(.+)",
        r"Supplier\s*[:#]?\s*(.+)",
        r"From\s*[:#]?\s*(.+)",
    ], text)

    date_text = first_match([
        r"Invoice Date\s*[:#]?\s*(.+)",
        r"Date\s*[:#]?\s*(.+)",
        r"Issued\s*[:#]?\s*(.+)",
    ], text)

    date = None

    if date_text:
        try:
            date = parse(date_text, dayfirst=True).date().isoformat()
        except:
            pass

    subtotal = first_match([
        r"Subtotal\s*[:#]?\s*(.+)",
        r"Net Amount\s*[:#]?\s*(.+)",
        r"Amount Before Tax\s*[:#]?\s*(.+)",
    ], text)

    tax = first_match([
        r"GST[^\n]*[:#]?\s*(.+)",
        r"IGST[^\n]*[:#]?\s*(.+)",
        r"CGST[^\n]*[:#]?\s*(.+)",
        r"SGST[^\n]*[:#]?\s*(.+)",
        r"VAT[^\n]*[:#]?\s*(.+)",
        r"Tax[^\n]*[:#]?\s*(.+)",
    ], text)

    currency = None

    if re.search(r"\bINR\b|Rs\.?|₹", text, re.IGNORECASE):
        currency = "INR"
    elif re.search(r"\bUSD\b|\$", text):
        currency = "USD"
    elif re.search(r"\bEUR\b|€", text):
        currency = "EUR"
    elif re.search(r"\bGBP\b|£", text):
        currency = "GBP"

    return {
        "invoice_no": invoice_no,
        "date": date,
        "vendor": vendor,
        "amount": parse_amount(subtotal),
        "tax": parse_amount(tax),
        "currency": currency,
    }

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


def search(pattern, text):
    m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else None


def parse_amount(value):
    if value is None:
        return None

    value = (
        value.replace(",", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .replace("INR", "")
        .replace("$", "")
        .strip()
    )

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

    invoice_no = search(
        r"Invoice\s*(?:No|Number)?\s*[:#-]?\s*([^\n]+)",
        text,
    )

    vendor = search(
        r"Vendor\s*[:#-]?\s*([^\n]+)",
        text,
    )

    date_text = search(
        r"Date\s*[:#-]?\s*([^\n]+)",
        text,
    )

    date = None

    if date_text:
        try:
            date = parse(date_text, dayfirst=True).date().isoformat()
        except:
            date = None

    subtotal = search(
        r"Subtotal\s*[:#-]?\s*(?:Rs\.?|INR|\$)?\s*([0-9,]+(?:\.[0-9]+)?)",
        text,
    )

    tax = search(
        r"(?:GST|Tax|VAT)[^\n]*[:#-]?\s*(?:Rs\.?|INR|\$)?\s*([0-9,]+(?:\.[0-9]+)?)",
        text,
    )

    currency = None

    if re.search(r"\bINR\b|Rs\.?", text, re.IGNORECASE):
        currency = "INR"
    elif "$" in text:
        currency = "USD"
    elif "EUR" in text:
        currency = "EUR"

    return {
        "invoice_no": invoice_no,
        "date": date,
        "vendor": vendor,
        "amount": parse_amount(subtotal),
        "tax": parse_amount(tax),
        "currency": currency,
    }

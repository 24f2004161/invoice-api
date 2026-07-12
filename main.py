import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

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


@app.get("/")
def root():
    return {"status": "running"}


@app.post("/extract")
def extract(req: InvoiceRequest):

    prompt = f"""
You are an expert invoice information extraction system.

Extract information ONLY from the invoice text below.

Invoice Text:

{req.invoice_text}

Return ONLY valid JSON.

The JSON MUST contain exactly these six keys:

{{
  "invoice_no": string | null,
  "date": string | null,
  "vendor": string | null,
  "amount": number | null,
  "tax": number | null,
  "currency": string | null
}}

Rules:

1. invoice_no
- Extract only the invoice identifier.
- Remove labels like:
  - Invoice No
  - Invoice Number
  - Invoice #
  - Ref
  - Reference
  - Bill No
- Example:
    Ref: UV-8810
becomes
    "UV-8810"

2. date
Return in ISO format:
YYYY-MM-DD

3. vendor
Return ONLY the company/vendor/seller/supplier name.

4. amount
Return ONLY the subtotal BEFORE tax.

Never return the grand total.

5. tax
Return ONLY the tax amount.

Ignore total.

6. currency

Return ISO currency code.

Examples:

Rs
₹
INR
-> INR

$
USD
-> USD

€
EUR
-> EUR

£
GBP
-> GBP

If a field is missing return null.

Do NOT wrap the JSON in markdown.

Return ONLY JSON.
"""

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )

    try:
        data = json.loads(response.text)
    except Exception:
        data = {}

    return {
        "invoice_no": data.get("invoice_no"),
        "date": data.get("date"),
        "vendor": data.get("vendor"),
        "amount": data.get("amount"),
        "tax": data.get("tax"),
        "currency": data.get("currency"),
    }

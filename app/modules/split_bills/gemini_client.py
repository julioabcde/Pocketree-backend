import base64
import json
from decimal import Decimal, InvalidOperation

import httpx
from loguru import logger

from app.core.config import settings

__all__ = ["parse_receipt", "is_available"]


_GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)

_RECEIPT_PROMPT = """
You are a receipt parsing assistant. Analyze the receipt image and extract structured data.

Return ONLY a valid JSON object. No explanation, markdown, or extra text.
{
  "items": [
    { "name": "string", "qty": number, "unit_price": number }
  ],
  "charges": [
    { "type": "tax|service|discount", "name": "string", "amount": number }
  ]
}

[ITEMS RULES]
- Include every purchased product, food, and drink line.
- "name": clean display name. Remove SKU, barcode prefixes, internal codes, and trailing symbols.
- "qty": integer quantity from receipt. Default to 1 if missing.
- "unit_price": price per single unit, not line total. If only line total is shown and qty > 1, divide it.
- Do NOT include subtotal, total, tax, discount, service charge, rounding, cash, or change lines as items.

[CHARGES RULES]
- Extract tax, service charge, and discount lines as charges (bill-level, not per-item).
- "type" must be exactly one of: "tax", "service", "discount".
- Use "tax" for PPN, VAT, GST, pajak, and similar lines.
- Use "service" for service charge, biaya layanan, and similar lines.
- Use "discount" for potongan, diskon, promo, and similar lines.
- "name": clean human-readable label, for example "PPN 11%" or "Service Charge".
- "amount": absolute amount already shown on receipt. Always positive, including discounts.
- If percentage and computed amount are both shown, use computed amount.
- If only percentage is shown, calculate amount from items subtotal.
- If no charges exist, return "charges": [].

[GENERAL RULES]
- Monetary values must be plain numbers with no currency symbols or thousand separators.
- If a line is ambiguous (for example rounding, change, or cash), omit it.
- If the receipt is partially unclear, do the best extraction from visible text.
""".strip()


def is_available() -> bool:
    return bool(settings.gemini_api_key)


async def parse_receipt(image_bytes: bytes, mime_type: str) -> dict:
    if not is_available():
        raise RuntimeError("GEMINI_API_KEY is not configured")

    url = _GEMINI_ENDPOINT.format(model=settings.gemini_model)
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": _RECEIPT_PROMPT},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(image_bytes).decode(),
                        }
                    },
                ]
            }
        ]
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            url,
            params={"key": settings.gemini_api_key},
            json=payload,
        )

    if response.status_code != 200:
        logger.error(
            f"Gemini API error {response.status_code}: {response.text[:500]}"
        )
        raise RuntimeError(f"Gemini API returned {response.status_code}")

    data = response.json()

    try:
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        logger.warning(f"Unexpected Gemini response shape: {data}")
        return {"items": [], "charges": []}

    return _parse_raw(raw_text)


def _parse_raw(raw: str) -> dict:
    try:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            return {"items": [], "charges": []}

        payload = json.loads(cleaned[start : end + 1])

        items = []
        for entry in payload.get("items") or []:
            try:
                unit_price = Decimal(str(entry["unit_price"]))
                if unit_price <= 0:
                    continue
                qty_raw = entry.get("qty", 1)
                qty = int(qty_raw) if qty_raw is not None else 1
                if qty < 1:
                    qty = 1
                items.append(
                    {
                        "name": str(entry["name"]).strip(),
                        "qty": qty,
                        "unit_price": unit_price,
                    }
                )
            except (KeyError, TypeError, InvalidOperation, ValueError):
                continue

        charges = []
        for entry in payload.get("charges") or []:
            try:
                amount = Decimal(str(entry["amount"]))
                if amount <= 0:
                    continue
                charges.append(
                    {
                        "type": str(entry["type"]).strip().lower(),
                        "name": str(entry["name"]).strip(),
                        "amount": amount,
                    }
                )
            except (KeyError, TypeError, InvalidOperation, ValueError):
                continue

        return {"items": items, "charges": charges}
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse Gemini response: {e}")
        return {"items": [], "charges": []}

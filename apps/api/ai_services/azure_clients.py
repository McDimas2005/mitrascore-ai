import json
import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class AzureAIClientError(Exception):
    pass


def _json_request(url, method="GET", headers=None, data=None, timeout=30):
    request = Request(url, data=data, method=method, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
            if not payload:
                return {}, response.headers
            return json.loads(payload.decode("utf-8")), response.headers
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AzureAIClientError(f"Azure request failed with HTTP {exc.code}: {body[:500]}") from exc
    except (URLError, TimeoutError) as exc:
        raise AzureAIClientError(f"Azure request failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise AzureAIClientError("Azure returned a non-JSON response.") from exc


def _normalize_endpoint(endpoint):
    return endpoint.rstrip("/")


def _average(values):
    clean = [float(value) for value in values if value is not None]
    return round(sum(clean) / len(clean), 2) if clean else 0.0


def _safe_text(value):
    return str(value or "").strip()


def _money_to_number(value):
    if isinstance(value, dict):
        amount = value.get("amount") or value.get("value") or value.get("content")
    else:
        amount = value
    text = str(amount or "")
    digits = re.sub(r"[^\d,.-]", "", text).replace(".", "").replace(",", ".")
    try:
        parsed = Decimal(digits)
    except (InvalidOperation, ValueError):
        return None
    return int(parsed) if parsed == parsed.to_integral_value() else float(parsed)


def _document_field_content(field):
    if not isinstance(field, dict):
        return ""
    value = (
        field.get("content")
        or field.get("valueString")
        or field.get("valueDate")
        or field.get("valuePhoneNumber")
        or field.get("valueNumber")
        or field.get("valueInteger")
    )
    if isinstance(value, dict):
        return value.get("content") or ""
    return _safe_text(value)


@dataclass
class AzureVisionClient:
    endpoint: str
    key: str
    service_name: str = "AzureVisionClient"

    def analyze_image(self, file_obj, filename, evidence_type, mime_type):
        if not self.endpoint or not self.key:
            raise AzureAIClientError("Azure AI Vision endpoint/key are not configured.")
        file_obj.open("rb")
        try:
            image_bytes = file_obj.read()
        finally:
            file_obj.close()
        if not image_bytes:
            raise AzureAIClientError("Uploaded image is empty.")

        query = urlencode(
            {
                "api-version": "2024-02-01",
                "features": "caption,denseCaptions,tags,read,objects",
                "language": "en",
                "gender-neutral-caption": "true",
            }
        )
        url = f"{_normalize_endpoint(self.endpoint)}/computervision/imageanalysis:analyze?{query}"
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": mime_type or "application/octet-stream",
        }
        raw, _headers = _json_request(url, method="POST", headers=headers, data=image_bytes)

        caption = raw.get("captionResult") or {}
        tags = raw.get("tagsResult", {}).get("values", []) or []
        objects = raw.get("objectsResult", {}).get("values", []) or []
        read_blocks = raw.get("readResult", {}).get("blocks", []) or []
        signage_lines = []
        for block in read_blocks:
            for line in block.get("lines", []) or []:
                text = _safe_text(line.get("text"))
                if text:
                    signage_lines.append(text)

        tag_names = [_safe_text(tag.get("name")).lower() for tag in tags]
        object_names = [_safe_text(obj.get("tags", [{}])[0].get("name")).lower() for obj in objects if obj.get("tags")]
        context_terms = " ".join(tag_names + object_names + signage_lines).lower()
        indicators = []
        if any(term in context_terms for term in ["store", "shop", "market", "retail", "sign", "shelf", "counter", "warung", "toko"]):
            indicators.append("konteks toko/warung terdeteksi")
        if any(term in context_terms for term in ["food", "product", "bottle", "package", "shelf", "stock", "inventory", "goods"]):
            indicators.append("stok atau produk terlihat")
        if signage_lines:
            indicators.append("teks/signage usaha terdeteksi")
        if evidence_type == "BUSINESS_PHOTO":
            indicators.append("bukti visual keberadaan usaha")

        flags = []
        caption_confidence = float(caption.get("confidence") or 0)
        if caption_confidence and caption_confidence < 0.55:
            flags.append("Kualitas foto rendah atau konteks visual kurang jelas.")
        if any(term in context_terms for term in ["blurry", "dark", "low light"]):
            flags.append("Foto mungkin buram atau kurang terang.")
        if not indicators:
            flags.append("Indikator visual usaha terbatas; perlu review manusia.")

        safe_tags = [
            tag.get("name")
            for tag in tags
            if tag.get("confidence", 0) >= 0.55
            and _safe_text(tag.get("name")).lower() not in {"person", "man", "woman", "boy", "girl", "face"}
        ][:8]
        confidence = _average([caption.get("confidence")] + [tag.get("confidence") for tag in tags[:8]])
        return {
            "indicators": list(dict.fromkeys(indicators)),
            "quality_flags": flags,
            "confidence": confidence or 0.5,
            "business_context": _safe_text(caption.get("text")),
            "possible_product_category": safe_tags,
            "inventory_stock_presence": any("stok" in item or "produk" in item for item in indicators),
            "storefront_business_context": any("konteks" in item or "keberadaan" in item for item in indicators),
            "signage_text": signage_lines[:8],
            "raw_response": raw,
        }


@dataclass
class AzureDocumentIntelligenceClient:
    endpoint: str
    key: str
    service_name: str = "AzureDocumentIntelligenceClient"

    def extract_document(self, file_obj, filename, evidence_type, mime_type):
        if not self.endpoint or not self.key:
            raise AzureAIClientError("Azure Document Intelligence endpoint/key are not configured.")
        model_id = {
            "RECEIPT": "prebuilt-receipt",
            "INVOICE": "prebuilt-invoice",
        }.get(evidence_type, "prebuilt-read")
        file_obj.open("rb")
        try:
            document_bytes = file_obj.read()
        finally:
            file_obj.close()
        if not document_bytes:
            raise AzureAIClientError("Uploaded document is empty.")

        query = urlencode({"api-version": "2024-11-30", "locale": "id-ID", "stringIndexType": "textElements"})
        url = f"{_normalize_endpoint(self.endpoint)}/documentintelligence/documentModels/{model_id}:analyze?{query}"
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": mime_type or "application/octet-stream",
        }
        _raw, response_headers = _json_request(url, method="POST", headers=headers, data=document_bytes)
        operation_url = response_headers.get("Operation-Location")
        if not operation_url:
            raise AzureAIClientError("Azure Document Intelligence did not return an Operation-Location header.")

        poll_headers = {"Ocp-Apim-Subscription-Key": self.key}
        final = {}
        for _attempt in range(10):
            time.sleep(1)
            final, _headers = _json_request(operation_url, headers=poll_headers)
            status = final.get("status", "").lower()
            if status == "succeeded":
                break
            if status == "failed":
                raise AzureAIClientError(f"Azure Document Intelligence analysis failed: {final.get('error')}")
        else:
            raise AzureAIClientError("Azure Document Intelligence analysis timed out.")

        analyze = final.get("analyzeResult", {}) or {}
        content = _safe_text(analyze.get("content"))
        documents = analyze.get("documents", []) or []
        fields = documents[0].get("fields", {}) if documents else {}
        pages = analyze.get("pages", []) or []
        lines = [_safe_text(line.get("content")) for page in pages for line in page.get("lines", []) or []]
        lines = [line for line in lines if line]

        amount = self._extract_amount(fields, content)
        merchant = self._extract_merchant(fields, lines)
        date = self._extract_date(fields, content)
        items = self._extract_items(fields, lines)
        confidences = [documents[0].get("confidence")] if documents else []
        confidences.extend(field.get("confidence") for field in fields.values() if isinstance(field, dict))
        confidence = _average(confidences) or 0.55

        flags = []
        if confidence < 0.6:
            flags.append("Confidence OCR rendah; perlu verifikasi manual.")
        if not content or len(content) < 20:
            flags.append("Teks OCR sangat terbatas.")
        if amount is None and evidence_type in {"RECEIPT", "INVOICE", "QRIS_SCREENSHOT"}:
            flags.append("Nominal transaksi belum terdeteksi jelas.")

        indicators = []
        if amount is not None:
            indicators.append("nominal transaksi terdeteksi")
        if merchant:
            indicators.append("merchant/supplier terdeteksi")
        if items:
            indicators.append("baris item transaksi terdeteksi")
        if evidence_type == "QRIS_SCREENSHOT":
            indicators.append("bukti kanal pembayaran digital")

        extracted_fields = {
            "amount": amount,
            "date": date,
            "merchant_or_supplier": merchant,
            "items": items,
            "model_id": model_id,
        }
        return {
            "extracted_text": content or "\n".join(lines[:12]),
            "extracted_fields": {key: value for key, value in extracted_fields.items() if value not in ("", None, [])},
            "indicators": list(dict.fromkeys(indicators)),
            "quality_flags": flags,
            "confidence": confidence,
            "raw_response": final,
        }

    def _extract_amount(self, fields, content):
        for key in ("Total", "InvoiceTotal", "AmountDue", "Subtotal"):
            field = fields.get(key)
            if isinstance(field, dict):
                value = _money_to_number(field.get("valueCurrency") or field.get("content"))
                if value is not None:
                    return value
        matches = re.findall(r"(?:rp|idr)?\s*([0-9][0-9.,]{3,})", content, flags=re.IGNORECASE)
        values = [_money_to_number(match) for match in matches]
        values = [value for value in values if value is not None]
        return max(values) if values else None

    def _extract_merchant(self, fields, lines):
        for key in ("MerchantName", "VendorName", "VendorAddress", "MerchantAddress"):
            text = _document_field_content(fields.get(key))
            if text:
                return text
        return lines[0] if lines else ""

    def _extract_date(self, fields, content):
        for key in ("TransactionDate", "InvoiceDate", "DueDate"):
            text = _document_field_content(fields.get(key))
            if text:
                return text
        match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", content)
        return match.group(1) if match else ""

    def _extract_items(self, fields, lines):
        field = fields.get("Items")
        items = []
        if isinstance(field, dict):
            values = field.get("valueArray") or []
            for value in values[:10]:
                item_obj = value.get("valueObject", {}) if isinstance(value, dict) else {}
                description = _document_field_content(item_obj.get("Description"))
                if description:
                    items.append(description)
        if items:
            return items
        return [line for line in lines[1:8] if not re.search(r"\b(total|subtotal|rp|idr)\b", line, re.IGNORECASE)][:6]

# Dummy Evidence Generation Prompt

Use this prompt in GPT to create realistic local dummy files for MitraScore AI uploads. Ask GPT to produce downloadable files when the chat tool supports file creation, or to produce file contents that you can save locally.

```text
You are helping me create realistic dummy UMKM business evidence files for a local fintech demo called MitraScore AI.

Create a complete evidence pack for an Indonesian UMKM owner. The files must be fake, safe for demo use, and must not include real personal data, real bank account numbers, real national ID numbers, real QR codes, or real customer identities.

Business profile:
- Owner name: Pak Andi
- Business name: Toko Andi Jaya
- Location: Garut, Jawa Barat
- Business category: warung sembako and small household goods
- Business duration: 18 months
- Financing purpose: add inventory stock before Ramadan
- Requested financing amount: Rp 7.500.000
- Estimated monthly revenue: Rp 15.000.000
- Estimated monthly expense: Rp 10.800.000
- No collateral
- No formal bank credit history
- No formal financial statement

Generate these dummy files:

1. business_photo_toko_andi_jaya.txt
   Content should describe a business photo in OCR-friendly text form:
   - storefront condition
   - visible stock
   - business activity
   - signage or location clue
   This file stands in for a photo upload during local testing.

2. supplier_receipt_beras_minyak_001.txt
   A supplier receipt in Bahasa Indonesia with:
   - fake supplier name
   - date
   - invoice/receipt number
   - item list: beras, minyak goreng, gula, mie instan
   - subtotal and total
   - payment status
   Use clearly fake phone/address details.

3. supplier_receipt_sembako_002.txt
   Another supplier receipt with different items and date.

4. daily_sales_note_toko_andi_jaya.txt
   A simple handwritten-style sales note in Bahasa Indonesia:
   - daily revenue estimates for 7 days
   - daily expense estimates
   - short cashflow note
   - explanation that the owner does not have formal financial statements

5. qris_transaction_summary_toko_andi_jaya.txt
   A fake QRIS transaction summary:
   - no real QR code
   - no real account number
   - daily transaction counts
   - total incoming amount
   - small repeated retail payments
   - disclaimer that it is dummy demo data

6. field_agent_observation_note.txt
   A field-agent note in Bahasa Indonesia:
   - inventory observed
   - customer traffic
   - supplier receipt checked
   - financing purpose verified
   - remaining questions for analyst

Output format:
- Provide each file with a clear filename heading.
- Put each file's exact contents in a separate fenced code block.
- Keep the content plain text so I can save each block as a .txt file and upload it to MitraScore AI.
- Make the evidence realistic enough for OCR/mock AI extraction but explicitly fictional.
- Do not include any protected attributes, biometric data, face descriptions, social media data, real identity numbers, or real payment credentials.
```

Suggested MitraScore evidence type mapping:

- `business_photo_toko_andi_jaya.txt`: `BUSINESS_PHOTO`
- `supplier_receipt_beras_minyak_001.txt`: `RECEIPT`
- `supplier_receipt_sembako_002.txt`: `RECEIPT`
- `daily_sales_note_toko_andi_jaya.txt`: `SALES_NOTE`
- `qris_transaction_summary_toko_andi_jaya.txt`: `QRIS_SCREENSHOT`
- `field_agent_observation_note.txt`: use as field-agent observation note, or upload as `OTHER`

Also create one simple dummy JPG-style image prompt for business_photo_toko_andi_jaya.jpg, but ensure it contains no faces, no real people, no license plates, and no real personal data.

business_photo_toko_andi_jaya.jpg → BUSINESS_PHOTO
qris_transaction_summary_toko_andi_jaya.png → QRIS_SCREENSHOT
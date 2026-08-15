# Local Data Import

The selected no-Firebase dashboard can process input files without Firestore,
Cloud Run polling, or a browser credential. The browser parses the file and
sends the rows to the local Python ledger API. The API validates and merges the
uploaded dataset with the reproducible fixtures, then returns a fresh finance
run directly to the dashboard.

## Start the Local Services

Open two terminals from the repository root:

```powershell
# Terminal 1: deterministic local import API
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn local_api:app --host 127.0.0.1 --port 8000
```

```powershell
# Terminal 2: dashboard
cd frontend
npm run dev
```

Open the Vite URL, then choose **Upload data**. The result replaces the visible
dashboard state immediately. It does not write to a cloud database.

## Accepted Files

| File | Behaviour |
| --- | --- |
| `template.xlsx` | Replaces each dataset represented by a worksheet. Omitted supporting datasets remain from the baseline fixtures. |
| `payments.csv` | Replaces the payment dataset only; it is the quickest way to demonstrate a changed collection or outstanding total. |
| `<dataset>.csv` | Replaces one supported dataset, where the name is `students`, `fee_items`, `concessions`, `waivers`, `payments`, `payment_plans`, `payment_history`, `refunds`, `transfers`, or `manual_adjustments`. |

A payment CSV needs these headers:

```text
paymentId,studentId,invoiceRef,date,amountPaise,mode,rawNarration
```

Amounts remain integer paise. For example, `2000000` means Rs. 20,000. A CSV
replaces its named dataset rather than appending to it, which avoids silently
double-counting an uploaded payment alongside a fixture payment.

## Guardrails

- Maximum local import size is 5,000 rows per dataset.
- Unsupported worksheet or file names and invalid numeric or structured fields
  are rejected with a visible error.
- Excel fields such as `lateFeePolicy` and payment-plan `installments` are
  normalized before the ledger runs.
- Importing data never activates Gemini wording, changes the original fixture
  files, writes to Firestore, or sends a message.

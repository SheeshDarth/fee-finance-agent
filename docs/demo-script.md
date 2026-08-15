# Assessment Demonstration Script

Use this as the presentation sequence.

## 1. Start the Local Demo

From the repository root:

\`\`\`powershell
.\\backend\\venv\\Scripts\\python.exe backend\\agent_runner.py --as-of 2026-08-13
cd backend
.\\venv\\Scripts\\Activate.ps1
python -m uvicorn local_api:app --host 127.0.0.1 --port 8000
cd ..\\frontend
npm run dev
\`\`\`

Open \`http://127.0.0.1:5173\`.

Expected dashboard figures:

- Net due: Rs. 121,335
- Verified collected: Rs. 55,500
- Outstanding: Rs. 65,835
- Overdue: Rs. 47,835
- Late fees: Rs. 1,835
- Pending human review: Rs. 19,000

## 2. Show the Required Outputs

1. **Overview**: show class exposure, fee-head exposure, late fees, ageing buckets, and the verified-ledger callout.
2. **Payment review**: show P003 as a possible Khan match and P004 as unmatched. Explain that both are excluded from official collections until a reviewer decides.
3. **Collection worklist**: show Kabir Khan, Aarav Sharma, and Meera Iyer. Point out the score, ageing bucket, payment-history reason, and Kabir's approved-plan contact suppression.
4. **Reminder drafts**: show the 31-60 day firm reminder and the 0-30 day polite reminder. Point out the exact due date, amount, validation status, and source. The deterministic run shows `DETERMINISTIC_TEMPLATE`; the live `--llm` run shows `GEMINI` with the same validator.
5. **Forecast & controls**: show the 30-day estimate as LOW confidence, the likely-delay cases, and the transfer/refund/adjustment/payment exception queue. Explain that a finding is not a proven loss and never alters a balance.
6. **Audit trail**: show run start, reconciliation decisions, student positions, forecast/control events, reminder creation, and run completion.
7. **Responsive UI**: resize to a mobile width and show the wrapped navigation, stacked header controls, two-column metrics, and scroll-contained data tables.
8. **Local import**: upload `payments.csv` or the supplied `template.xlsx`; show that the dashboard refreshes from the Python ledger immediately, without Firebase polling.

## 3. Explain the Money Safety Boundary

State that Python calculates all money in integer paise. Gemini, when enabled, receives the already-calculated amount and due date only to word a message. The validator rejects any changed or invented monetary figure or date. Reminders are drafts and are never sent automatically.

## 4. Live Cloud Run Agent Demonstration

1. Keep the React dashboard in local demo mode; do not add Firebase configuration.
2. Sign in to the company GCP project with `gcloud auth login`.
3. Run:

\`\`\`powershell
.\backend\scripts\invoke_cloud_run_agent.ps1
\`\`\`

4. Explain that the script invokes the private Cloud Run ADK API using a short-lived IAM identity token.
5. Point out the tools selected by Gemini: cash forecast and leakage findings. Their monetary facts originate in deterministic Python, so the model only explains returned evidence.
6. For reminder wording, run `python agent_runner.py --as-of 2026-08-13 --llm` with ADC. The same exact amount-and-date validator applies.

## 5. What Is Still External

The source code, local dashboard, and live Cloud Run ADK validation are complete. Firebase/Firestore is deliberately not part of the company deployment. There is not yet a persistent company data store, scheduled job, browser-to-private-API proxy, or production reviewer workflow; these are documented honestly in `docs/no-firebase-operating-mode.md`.

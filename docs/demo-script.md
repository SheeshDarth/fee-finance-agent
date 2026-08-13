# Assessment Demonstration Script

Use this as the presentation sequence.

## 1. Start the Local Demo

From the repository root:

\`\`\`powershell
.\\backend\\venv\\Scripts\\python.exe backend\\agent_runner.py --as-of 2026-08-13
cd frontend
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
4. **Reminder drafts**: show the 31-60 day firm reminder and the 0-30 day polite reminder. Point out the exact due date, amount, validation status, and \`DETERMINISTIC_TEMPLATE\` source.
5. **Audit trail**: show run start, reconciliation decisions, student positions, reminder creation, and run completion.
6. **Responsive UI**: resize to a mobile width and show the wrapped navigation, stacked header controls, two-column metrics, and scroll-contained data tables.

## 3. Explain the Money Safety Boundary

State that Python calculates all money in integer paise. Gemini, when enabled, receives the already-calculated amount and due date only to word a message. The validator rejects any changed or invented monetary figure or date. Reminders are drafts and are never sent automatically.

## 4. Optional Live Demonstration

1. Enable Firebase Authentication Email/Password.
2. Create a reviewer user.
3. Add \`reviewers/{uid}\` with \`active: true\` in Firestore.
4. Copy Firebase web values into \`frontend/.env\`.
5. Start the worker:

\`\`\`powershell
cd backend
.\\venv\\Scripts\\Activate.ps1
python firestore_worker.py
\`\`\`

6. Sign in in the dashboard and click **Run live workflow**.
7. Show the Firestore-backed status changing from \`PENDING\` to \`RUNNING\` and then \`AWAITING_REVIEW\`.
8. Open Payment review and record a reviewer action. Show the new action and audit event.
9. For Gemini wording, set \`ENABLE_LLM=true\` or run \`python agent_runner.py --llm\`. A deterministic fallback is expected when Vertex AI permissions or API access are unavailable.

## 5. What Is Still External

The source code and local assessment workflow are complete. The only steps outside the repository are Firebase web configuration, reviewer-user creation, Firestore deployment, and Vertex AI IAM/API enablement. These require the project owner's cloud-console access and are intentionally not represented by fake local data.


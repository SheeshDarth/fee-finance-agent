# Council Readiness Verdict

The five-advisor council reviewed the repository, assessment requirements, cloud state, financial controls, and evaluator experience on 2026-08-13.

## Verdict

**Ready for a strong, scoped technical assessment walkthrough.** The prototype demonstrates a practical AI workflow, deterministic financial handling, modular code, usable local dashboard output, Google ADK integration, and a live-validated Vertex AI Cloud Run agent.

**Not ready to claim production completion.** The supplied company project has a verified Cloud Run ADK deployment, but still needs a least-privilege runtime identity, persistent company data source, scheduled execution, and multi-user reviewer workflow. Firebase is intentionally not selected.

## What The Council Found Strong

- The ledger is deterministic and uses integer paise.
- Ambiguous payments are explicitly excluded from verified collections.
- Instalment schedules, late fees, concessions, waivers, plans, payment history, and audit events are visible.
- Gemini is constrained to wording and validated against exact amount and due date.
- The ADK wrapper exposes read-only tools around the deterministic workflow.
- The evidence, diagrams, limitations, and demo script make the design explainable.

## Canonical Walkthrough

1. Run the deterministic command and state the expected totals.
2. Show Overview and explain net due, collected, outstanding, overdue, late fees, and ageing.
3. Show P003/P004 in Payment review and explain the confidence gate.
4. Show history-based worklist scores and Kabir's plan-compliance suppression.
5. Show two ageing-bucket reminder drafts and their exact amount/date validation.
6. Run `--llm` and show `generationSource: GEMINI` plus `validationPassed: true`.
7. Open ADK locally and explain that its tools are read-only.
8. Run `backend/scripts/invoke_cloud_run_agent.ps1` and show the live Vertex tool call.
9. Close with the no-Firebase operating decision and explicit limitations.

## Evidence Checklist

Use `docs/walkthrough-evidence.md` for requirement traceability, `docs/verification-transcript.md` for exact checks, and `docs/company-cloud-status.md` for honest cloud provenance. The evaluator should see both capability and engineering judgment about what is not yet verified.

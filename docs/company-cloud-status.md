# Company Cloud Status

Checked on 2026-08-15. This note is the source of truth for the only intended deployment target: `intern-bnmit-july-2026`.

## Company Project: `intern-bnmit-july-2026`

- Project exists: yes. Project number: `444451720807`.
- Billing: enabled.
- Enabled APIs: Vertex AI, Firestore, Cloud Run, Cloud Build, Artifact Registry, and Cloud Storage.
- Firestore database: not created. It is not required under the administrator's no-Firebase deployment decision.
- Firebase registration: not completed. It is intentionally out of scope for the company project.
- Cloud Run: FeeOps ADK API is deployed and Ready as `feeops-backend-00007-tl4` at `https://feeops-backend-pohamtwcgq-uc.a.run.app`. An authenticated 2026-08-15 smoke test used Vertex AI Gemini, selected the cash-forecast and leakage tools, and returned grounded output.
- Cloud Run runtime identity: the deployed service is temporarily using the default Compute Engine service account. It has sufficient Vertex access for the demonstrated ADK request, but it must be replaced with the documented least-privilege `feeops-runtime` identity before a production deployment.
- Cloud Run Job: not created. A future no-Firebase scheduled job may use Cloud Storage snapshots instead; see `no-firebase-operating-mode.md`.
- Local downloaded service-account key: it does not belong to this company project and must not be used.

Required administrator action for a hardened deployment: replace the temporary default Compute runtime identity with a least-privilege Cloud Run identity that has Vertex AI User. Firebase registration, Native Firestore, a Firebase Web App, and Firebase Authentication are not required. No downloaded JSON key is part of this architecture.

## Claims To Make In The Interview

Say: “The finance workflow, bounded ADK agent, and guarded Vertex Gemini integration are implemented and the agent is live on the supplied company Cloud Run project. The dashboard intentionally runs locally from a reproducible deterministic snapshot; Firebase is not part of this deployment.”

Do not say: “the company Firestore dashboard is live” or “the agent derives its production data from Firestore” until the activation and worker checks in the runbook pass.

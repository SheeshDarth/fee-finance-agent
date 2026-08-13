# Cloud Provenance and Current Status

Checked on 2026-08-13. This note separates what is verified in the company project from what is live-tested in the Firebase-enabled assessment project.

## Company Project: `intern-bnmit-july-2026`

- Project exists: yes. Project number: `444451720807`.
- Billing: enabled.
- Enabled APIs: Vertex AI, Firestore, Cloud Run, Cloud Build, Artifact Registry, and Cloud Storage.
- Firestore database: not created; the current identity receives permission denied.
- Firebase registration: not completed; `projects.addFirebase` returns 403 for the current identity.
- Agent Runtime: dry-run metadata works, but an actual deployment has not been completed because local ADC is not available and company deployment identity setup is pending.
- Local downloaded service-account key: belongs to `test1-457903`, not this company project. It must not be reused.

Required administrator action: register the company project in Firebase, create the Native Firestore `(default)` database, create the FeeOps Web App, enable Email/Password Authentication, create a least-privilege service account, and grant the deployment identity the Agent Runtime roles. Then replace local ignored credentials and repeat the runbook in `docs/company-cloud-deployment.md`.

## Live-Tested Assessment Project: `test1-457903`

- Billing: enabled on the Blaze plan.
- Firebase: registered with FeeOps Web App.
- Firestore: Native database and rules deployed.
- Authentication: Identity Platform initialized and Email/Password enabled on 2026-08-13.
- Gemini: live Vertex AI wording run succeeded on 2026-08-13; deterministic amount/date validation is still mandatory.
- Firestore worker: live-tested with PENDING -> AWAITING_REVIEW and published 4 positions, 5 reconciliation rows, 3 worklist rows, 2 reminder drafts, and 17 audit events.

This is the canonical live demo environment until the company project IAM setup is completed. It is not evidence that the company project has been deployed.

## Claims To Make In The Interview

Say: “The finance workflow, ADK wrapper, Firebase/Firestore path, and Gemini wording path are implemented and verified in the assessment project. The supplied company project is prepared with billing and APIs, but Firebase registration, Firestore creation, and managed deployment still require an administrator permission change.”

Do not say: “The agent is deployed to the company project” or “the company Firestore dashboard is live.” Those statements are not verified.

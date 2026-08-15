# Company Cloud Status

Checked on 2026-08-15. This note is the source of truth for the only intended deployment target: `intern-bnmit-july-2026`.

## Company Project: `intern-bnmit-july-2026`

- Project exists: yes. Project number: `444451720807`.
- Billing: enabled.
- Enabled APIs: Vertex AI, Firestore, Cloud Run, Cloud Build, Artifact Registry, and Cloud Storage.
- Firestore database: not created; the current identity receives permission denied.
- Firebase registration: not completed; `projects.addFirebase` returns 403 for the current identity.
- Cloud Run: the project contains existing services, but FeeOps has not yet been deployed with its dedicated runtime service account.
- Cloud Run Job: not yet created for the Firestore worker.
- Local downloaded service-account key: it does not belong to this company project and must not be used.

Required administrator action: register the company project in Firebase, create the Native Firestore `(default)` database, create the FeeOps Web App, enable Email/Password Authentication, create a least-privilege Cloud Run runtime service account, and grant deployment permissions. Then follow [company-cloud-deployment.md](company-cloud-deployment.md). No downloaded JSON key is part of this architecture.

## Claims To Make In The Interview

Say: “The finance workflow, ADK wrapper, Firebase/Firestore integration, and guarded Gemini wording are implemented. The supplied company project is prepared with billing and core APIs; Firebase registration and Native Firestore creation are pending the organization administrator permissions documented in the runbook.”

Do not say: “The FeeOps agent is deployed to the company project” or “the company Firestore dashboard is live” until the activation and deployment checks in the runbook pass.

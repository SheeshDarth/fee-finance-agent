# Company Cloud Deployment

This is the deployment runbook for the project named in Raghu Kumar's email: `intern-bnmit-july-2026`.

## Verified project state

- Project exists: `intern-bnmit-july-2026`.
- Billing is enabled.
- Enabled APIs include Vertex AI, Firestore, Cloud Run, Cloud Build, Artifact Registry, and Cloud Storage.
- Storage buckets already exist for Cloud Build and Cloud Run sources.
- The local key currently in this repository belongs to `test1-457903`; it must not be used for the company project.

## One-time console actions

The signed-in developer account can describe the project but cannot currently call Firebase `addFirebase` or create the Firestore database. A project administrator must do one of the following:

1. Firebase console: open `intern-bnmit-july-2026`, register it as a Firebase project, create the Native Firestore `(default)` database, create a FeeOps Web App, and enable Email/Password Authentication.
2. IAM: grant the developer account the project-level permissions needed for Firebase registration and Firestore database creation, or perform those two actions on the developer's behalf.

After that, create a service account in `intern-bnmit-july-2026` with least-privilege Vertex AI User, Cloud Datastore User, and required Agent Runtime deployment roles. Download its JSON key to `backend/service-account.json`; keep it ignored by Git.

## ADK local verification

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
adk web feeops_adk
```

The agent's tools call the deterministic fee workflow. A failed Gemini call cannot change any money because the tools do not expose write access.

## Managed Agent Runtime deployment

```powershell
gcloud auth login
gcloud config set project intern-bnmit-july-2026
cd backend
agents-cli scaffold enhance . --deployment-target agent_runtime
agents-cli deploy --project intern-bnmit-july-2026 --region us-central1 --no-wait
agents-cli deploy --status --project intern-bnmit-july-2026 --region us-central1
```

The first deployment may take several minutes. Use the status command until it reaches a terminal state. If IAM rejects the deployment, grant the deployment service account the roles named in the Cloud Console error and rerun the same command.

## Firebase dashboard connection

After Firebase is registered, create the web app, copy its config into the ignored `frontend/.env`, deploy rules with `firebase deploy --only firestore:rules --project intern-bnmit-july-2026`, and create an active reviewer document at `reviewers/{uid}`. The React client then uses `onSnapshot` for the run document and all child collections.

# No-Firebase Operating Mode

## Decision

The company administrator has confirmed that `intern-bnmit-july-2026` must use
the deployed Cloud Run backend without registering the project in Firebase.
This document supersedes earlier company-project Firebase activation steps. The
Firebase/Firestore code remains an optional, previously tested integration; it
is not part of the company deployment or assessment claim.

## What Runs Today

| Component | Operating mode | Status |
| --- | --- | --- |
| FeeOps ADK backend | Private Cloud Run service using its attached GCP identity and Vertex AI | Live and verified |
| Finance input | Versioned JSON fixtures packaged with the service | Deterministic assessment source |
| React dashboard | Local Vite application reading `demo-output.json` | Supported primary demo path |
| Agent interaction | Local PowerShell client obtains a short-lived IAM token and calls Cloud Run | Included and verified |
| Firebase Auth, Firestore, live subscriptions | Not selected for the company project | Disabled by omission of `frontend/.env` |

Do not add `VITE_FIREBASE_*` values to the local frontend for this mode. The
dashboard automatically presents its local deterministic snapshot.

## Demonstrate the Live Agent

1. Authenticate with the GCP account that can invoke the service:

   ```powershell
   gcloud auth login
   gcloud config set project intern-bnmit-july-2026
   ```

   The demonstrator needs `roles/run.invoker` on `feeops-backend`. This role is
   for calling the private service; it is separate from the service's own
   Vertex AI runtime permissions.

2. From the repository root, invoke the deployed ADK service:

   ```powershell
   .\backend\scripts\invoke_cloud_run_agent.ps1
   ```

The script creates a disposable ADK session, uses an IAM identity token, and
prints the final Gemini response. It never reads a service-account file or a
Gemini API key. Ask a different evidence question with `-Prompt`, for example:

```powershell
.\backend\scripts\invoke_cloud_run_agent.ps1 -Prompt "Use the agent decisions and escalation tools. What is the next safe action for Kabir Khan?"
```

## Demonstrate the Dashboard

Run the local deterministic workflow, then Vite:

```powershell
.\backend\venv\Scripts\python.exe .\backend\agent_runner.py --as-of 2026-08-13
cd frontend
npm run dev
```

This is intentionally separate from the private Cloud Run service. A browser
cannot safely mint the user IAM token required by a private Cloud Run endpoint.
The dashboard demonstrates the same generated run data; the PowerShell client
demonstrates the live Vertex-backed agent.

## Alternatives for Later

| Need | Suitable no-Firebase option | Important boundary |
| --- | --- | --- |
| Persist versioned input and result runs | Cloud Storage objects such as `inputs/{runId}.json` and `runs/{runId}.json` | Add schema validation and immutable run IDs before using it for finance records. |
| Scheduled daily workflow | Cloud Scheduler starts a Cloud Run Job | The job should read one input snapshot and write one result snapshot. |
| Browser dashboard with fresh data | A small authenticated Cloud Run BFF that reads the latest result object | Do not make the existing finance API public just so a browser can reach it. |
| Strong multi-user workflow | Cloud SQL plus an authenticated Cloud Run BFF | More operational work, but better for relational finance data and reviewer history. |

Cloud Storage plus Cloud Scheduler and a Cloud Run Job is the recommended next
step if automation is required without Firebase. It is an architectural option,
not a completed feature in this prototype. Until it is implemented, do not
claim a live feed, event-driven runs, or a Firestore source of truth.

## Security Boundary

- Cloud Run remains IAM-protected.
- Vertex AI uses the service's attached identity, not a Gemini API key.
- The frontend contains no GCP credential and no direct private-API access.
- All money remains deterministic integer-paise Python output; Gemini only
  selects evidence tools and explains their returned facts.

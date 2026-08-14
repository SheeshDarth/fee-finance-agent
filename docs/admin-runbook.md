# FeeOps Agent – Admin Runbook

This document records the completed cloud setup and specifies exactly what a
project organization-administrator must do to fully activate the
`intern-bnmit-july-2026` project for the FeeOps agent.

---

## Live Credentials Summary

| Resource | Value |
|----------|-------|
| Personal Google account | `siddharthprashoo@gmail.com` |
| Own GCP project (data backend) | `test1-457903` |
| Company GCP project (hosting) | `intern-bnmit-july-2026` |
| ADK agent SA (test1) | `fee-agent-runner@test1-457903.iam.gserviceaccount.com` |
| Firebase project | `test1-457903` |
| Reviewer email | `reviewer@feeops.demo` |
| Reviewer password | `FeeOps-Demo-2026!` |
| Reviewer Firestore doc | `reviewers/m4mzMGLpCGTWLY51GV2BoglpCsl2` |
| Live Firestore finance run | `finance_runs/FK0LALjKHeBFh9XO4Rw7` |

---

## What Has Been Completed (No Admin Needed)

1. **Firestore database** — `test1-457903` (default, nam5) — Created 2026-08-13.
2. **Live finance run written** — `finance_runs/FK0LALjKHeBFh9XO4Rw7` — 2026-08-14.
3. **Firebase Email/Password Auth** — enabled in `test1-457903`.
4. **Reviewer Auth account** — `reviewer@feeops.demo` (uid `m4mzMGLpCGTWLY51GV2BoglpCsl2`).
5. **Reviewers Firestore doc** — `reviewers/m4mzMGLpCGTWLY51GV2BoglpCsl2` written.
6. **GitHub repository** — `https://github.com/SheeshDarth/fee-finance-agent` — branch `master` up to date.
7. **All 7 unit tests** — passing (`test_finance_invariants.py`).
8. **Cloud Run deploy** — `feeops-backend` deployed to `intern-bnmit-july-2026 / us-central1`.

---

## What an Org Admin Must Do to Fully Activate `intern-bnmit-july-2026`

The following steps require the organization administrator
(`project.manager@subhanu.com` or an org-level IAM admin) to run once.

### A. Grant IAM roles to `siddharthprashoo@gmail.com`

```bash
PROJECT=intern-bnmit-july-2026
ACCOUNT=siddharthprashoo@gmail.com

# Required to create service accounts and manage IAM
gcloud projects add-iam-policy-binding $PROJECT \
  --member="user:$ACCOUNT" \
  --role="roles/iam.serviceAccountAdmin"

# Required to create Firestore database
gcloud projects add-iam-policy-binding $PROJECT \
  --member="user:$ACCOUNT" \
  --role="roles/datastore.owner"

# Required to view IAM policy
gcloud projects add-iam-policy-binding $PROJECT \
  --member="user:$ACCOUNT" \
  --role="roles/resourcemanager.projectIamAdmin"
```

### B. Create Firestore Database in `intern-bnmit-july-2026`

After granting roles above:

```bash
gcloud firestore databases create \
  --location=us-central1 \
  --project=intern-bnmit-july-2026
```

### C. Create a Dedicated Service Account

```bash
PROJECT=intern-bnmit-july-2026

gcloud iam service-accounts create feeops-agent-runner \
  --display-name="FeeOps Agent Runner" \
  --project=$PROJECT

# Grant Firestore access
gcloud projects add-iam-policy-binding $PROJECT \
  --member="serviceAccount:feeops-agent-runner@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Grant Vertex AI access
gcloud projects add-iam-policy-binding $PROJECT \
  --member="serviceAccount:feeops-agent-runner@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Download key
gcloud iam service-accounts keys create backend/service-account-company.json \
  --iam-account="feeops-agent-runner@${PROJECT}.iam.gserviceaccount.com" \
  --project=$PROJECT
```

### D. Register Firebase in `intern-bnmit-july-2026`

Visit: https://console.firebase.google.com/  
→ Add project → Select existing GCP project `intern-bnmit-july-2026`  
→ Enable Email/Password Authentication  
→ Copy Web App config to `frontend/.env` (replacing `test1-457903` values)

### E. Re-deploy with Company SA

```bash
# Update backend/.env:
#   GOOGLE_APPLICATION_CREDENTIALS="service-account-company.json"
#   GCP_PROJECT_ID="intern-bnmit-july-2026"

gcloud run deploy feeops-backend \
  --source backend/ \
  --project=intern-bnmit-july-2026 \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=intern-bnmit-july-2026,GCP_LOCATION=us-central1,ENABLE_LLM=true,GEMINI_MODEL=gemini-2.5-flash"
```

### F. Deploy Managed Agent Runtime (optional — needs SA from step C)

```bash
cd backend
agents deploy --manifest agents-cli-manifest.yaml \
  --project=intern-bnmit-july-2026 \
  --service-account="feeops-agent-runner@intern-bnmit-july-2026.iam.gserviceaccount.com"
```

---

## Current Architecture

```
[Frontend: React/Vite]          [test1-457903]
   └─ firebase.js               ├─ Firebase Auth (Email/Password)
      └─ liveData.js            ├─ Firestore (finance_runs, reviewers)
                                └─ Vertex AI (gemini-2.5-flash)

[intern-bnmit-july-2026]
   └─ Cloud Run: feeops-backend
      └─ ADK Agent (feeops_adk)
         └─ tool: run_fee_workflow → calls test1-457903 resources
```

---

## Quick Demo Steps

1. Start frontend: `cd "FDE AGENT/frontend" && npm run dev`
2. Open `http://localhost:5173`
3. Sign in: `reviewer@feeops.demo` / `FeeOps-Demo-2026!`
4. Dashboard shows live finance data from `backend/output.json`
5. ADK agent chat: POST to Cloud Run service URL

---

*Last updated: 2026-08-14 by siddharthprashoo@gmail.com via Antigravity IDE*

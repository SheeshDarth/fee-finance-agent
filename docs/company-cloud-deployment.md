# Company Cloud Run Deployment

This is the only deployment runbook for FeeOps. All application resources must
use the company project `intern-bnmit-july-2026` in `us-central1`. Do not reuse
the earlier personal Firebase project or any downloaded JSON key.

## Current prerequisite status

- Billing and the required core APIs are enabled in `intern-bnmit-july-2026`.
- The current developer can select the project, but Firebase registration returns
  `403` and Native Firestore database creation returns permission denied.
- Therefore the organization administrator must complete the following one-time
  activation before the developer can deploy and validate FeeOps.

## 1. Administrator activation

The administrator should first register the existing Google Cloud project with
Firebase in the Firebase Console. Select **Add project**, choose
`intern-bnmit-july-2026`, and complete the registration. This action needs a
project Owner or Editor. If temporary Editor is granted to the developer for
this step, remove it immediately after registration.

Then create the Native Firestore `(default)` database in `us-central1` and, in
Firebase Authentication, enable the Email/Password provider. Create a Web App
named `FeeOps Dashboard` and retain its six SDK values for the developer.

The administrator can use this least-privilege IAM matrix. Replace
`DEVELOPER_EMAIL` with `siddharthprashoo@gmail.com` only if that is the intended
developer account.

| Principal | Scope | Role | Purpose |
|---|---|---|---|
| Developer | project, temporary | `roles/datastore.owner` | Create the Native Firestore database; remove after creation. |
| Developer | project | `roles/firebaseauth.admin` | Configure Email/Password authentication. |
| Developer | project | `roles/firebaserules.admin` | Deploy `firestore.rules`. |
| Developer | project | `roles/run.sourceDeveloper` | Deploy the Cloud Run service and job from source. |
| Developer | project | `roles/serviceusage.serviceUsageConsumer` | Use enabled Google APIs while deploying. |
| Developer | FeeOps runtime service account only | `roles/iam.serviceAccountUser` | Attach, but not administer, the runtime identity. |
| Runtime service account | project | `roles/datastore.user` | Read/write Firestore as the backend and worker. |
| Runtime service account | project | `roles/aiplatform.user` | Call Vertex AI Gemini for guarded reminder wording. |
| Build service account | project | `roles/run.builder` | Build Cloud Run source deployments. |

The admin should create the runtime identity rather than giving the developer
`iam.serviceAccountAdmin` or project IAM-admin rights:

```powershell
$PROJECT = "intern-bnmit-july-2026"
$DEVELOPER = "siddharthprashoo@gmail.com"
$RUNTIME = "feeops-runtime@$PROJECT.iam.gserviceaccount.com"
$PROJECT_NUMBER = "444451720807"
$BUILD = "$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud iam service-accounts create feeops-runtime `
  --project $PROJECT --display-name "FeeOps Cloud Run runtime"

gcloud projects add-iam-policy-binding $PROJECT `
  --member "serviceAccount:$RUNTIME" --role "roles/datastore.user"
gcloud projects add-iam-policy-binding $PROJECT `
  --member "serviceAccount:$RUNTIME" --role "roles/aiplatform.user"
gcloud projects add-iam-policy-binding $PROJECT `
  --member "serviceAccount:$BUILD" --role "roles/run.builder"

gcloud iam service-accounts add-iam-policy-binding $RUNTIME `
  --member "user:$DEVELOPER" --role "roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding $PROJECT `
  --member "user:$DEVELOPER" --role "roles/run.sourceDeveloper"
gcloud projects add-iam-policy-binding $PROJECT `
  --member "user:$DEVELOPER" --role "roles/serviceusage.serviceUsageConsumer"
gcloud projects add-iam-policy-binding $PROJECT `
  --member "user:$DEVELOPER" --role "roles/firebaserules.admin"
gcloud projects add-iam-policy-binding $PROJECT `
  --member "user:$DEVELOPER" --role "roles/firebaseauth.admin"
```

For the one-time database creation, either the admin creates it directly in the
console or temporarily grants `roles/datastore.owner` to the developer. The
database must be **Native mode**, database ID **`(default)`**, region
**`us-central1`**. Remove `roles/datastore.owner` after it is created.

## 2. Developer local configuration

From the repository root, authenticate to the company project. ADC is the only
local backend credential. Cloud Run uses the attached runtime identity; neither
uses a JSON service-account key.

```powershell
gcloud auth login
gcloud config set project intern-bnmit-july-2026
gcloud auth application-default login
firebase use intern-bnmit-july-2026

Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Set the six values from the company Firebase Web App in `frontend/.env`:

```dotenv
VITE_FIREBASE_API_KEY=
VITE_FIREBASE_AUTH_DOMAIN=
VITE_FIREBASE_PROJECT_ID=intern-bnmit-july-2026
VITE_FIREBASE_STORAGE_BUCKET=
VITE_FIREBASE_MESSAGING_SENDER_ID=
VITE_FIREBASE_APP_ID=
```

`frontend/.env` and `backend/.env` are ignored by Git. The Firebase web values
identify the public web app; they are not a server credential. Do not set
`GOOGLE_APPLICATION_CREDENTIALS` for this project.

## 3. Firebase, reviewer, and Firestore verification

Deploy the checked-in rules only after the database exists:

```powershell
firebase deploy --only firestore:rules --project intern-bnmit-july-2026

cd backend
..\backend\venv\Scripts\python.exe scripts\verify_firestore.py
```

Create an evaluator-owned reviewer account only after the Email/Password
provider and Web App configuration exist. Put the email and password in the
ignored `backend/.env`, then run:

```powershell
.\venv\Scripts\python.exe scripts\create_reviewer.py
```

The script creates the Auth user and writes `reviewers/{uid}` with
`active: true`; it does not print the password. The rules allow only active
reviewers to create a pending run or read its output.

## 4. Deploy the backend and worker to Cloud Run

Run these commands from the repository root. The API service is IAM-protected;
grant `roles/run.invoker` only to the reviewers or demonstrators who need direct
access. The React dashboard communicates with Firestore directly under its
Firebase rules, so it does not need an unauthenticated backend endpoint.

```powershell
$PROJECT = "intern-bnmit-july-2026"
$REGION = "us-central1"
$RUNTIME = "feeops-runtime@$PROJECT.iam.gserviceaccount.com"

gcloud run deploy feeops-adk-api `
  --source backend `
  --project $PROJECT `
  --region $REGION `
  --service-account $RUNTIME `
  --no-allow-unauthenticated `
  --set-env-vars "^@^GCP_PROJECT_ID=$PROJECT@GCP_LOCATION=$REGION@GOOGLE_CLOUD_PROJECT=$PROJECT@GOOGLE_CLOUD_LOCATION=$REGION@GOOGLE_GENAI_USE_VERTEXAI=true@ENABLE_LLM=true@GEMINI_MODEL=gemini-2.5-flash"

gcloud run jobs deploy feeops-firestore-worker `
  --source backend `
  --project $PROJECT `
  --region $REGION `
  --service-account $RUNTIME `
  --command python `
  --args firestore_worker.py,--once `
  --set-env-vars "^@^GCP_PROJECT_ID=$PROJECT@GCP_LOCATION=$REGION@GOOGLE_CLOUD_PROJECT=$PROJECT@GOOGLE_CLOUD_LOCATION=$REGION@GOOGLE_GENAI_USE_VERTEXAI=true@ENABLE_LLM=true@GEMINI_MODEL=gemini-2.5-flash"
```

The API invokes the Google ADK service. The Cloud Run Job processes only
pending Firestore runs, then exits. Execute it after an active reviewer creates
a run:

```powershell
gcloud run jobs execute feeops-firestore-worker `
  --project intern-bnmit-july-2026 --region us-central1 --wait
```

No service-account key, Gemini API key, or Firebase admin key is supplied to
Cloud Run. Vertex AI and Firestore obtain credentials from `feeops-runtime`.

## 5. Acceptance checks

1. `gcloud firestore databases list --project intern-bnmit-july-2026` shows
   `(default)` with Native mode.
2. The dashboard signs in with the created reviewer and can create one `PENDING`
   run.
3. The Cloud Run Job finishes successfully and changes it to
   `AWAITING_REVIEW`, with child collections for positions, reconciliation,
   reminders, decisions, escalations, and audit events.
4. `frontend` shows live `onSnapshot` data, including P003/P004 review cases
   and the `DRAFT_REMINDER` / `ESCALATE_FOR_REVIEW` decisions.
5. A Cloud Run API request with an identity token returns the read-only ADK
   tools; it cannot change money, send messages, or approve payments.

Use `docs/validation.md` for the evidence checklist. Do not claim a company
deployment until all five checks have been recorded.

# FeeOps Administrator Runbook

Target project: `intern-bnmit-july-2026`
Region: `us-central1`
Deployment platform: Cloud Run service plus Cloud Run Job

## Security decisions

- The company project is the sole FeeOps target. Do not use `test1-457903`.
- Cloud Run and local tools use Application Default Credentials. No
  service-account JSON key is created, downloaded, mounted, or committed.
- `feeops-runtime@intern-bnmit-july-2026.iam.gserviceaccount.com` is the only
  runtime identity. It has Firestore user and Vertex AI user access, not owner.
- Firebase client configuration is stored in ignored `frontend/.env`; it is
  public web-app metadata, not an administrative credential.
- The Firestore rules permit an authenticated active reviewer to submit a
  pending run and view output. The worker alone performs backend processing.

## One-time administrator work

1. Register the existing company project in Firebase.
2. Create Native Firestore `(default)` in `us-central1`.
3. Enable Firebase Authentication Email/Password and create the `FeeOps
   Dashboard` Web App.
4. Create the dedicated runtime service account and the IAM bindings listed in
   [company-cloud-deployment.md](company-cloud-deployment.md).
5. Provide the six Firebase Web App values to the developer through an approved
   channel. Never provide a service-account key.

The needed developer and runtime IAM roles, copy-paste commands, deployment
commands, and acceptance checks are intentionally centralized in
[company-cloud-deployment.md](company-cloud-deployment.md). This avoids the
previous unsafe combination of a personal Firebase project and a company Cloud
Run project.

## Ongoing operation

1. Reviewer signs into the dashboard and creates a `PENDING` run.
2. Operator executes the `feeops-firestore-worker` Cloud Run Job.
3. Worker publishes `AWAITING_REVIEW` data and audit events.
4. Reviewer validates payment exceptions and reminder drafts.
5. Any outbound collection communication happens outside this prototype after
   human review; FeeOps never sends it automatically.

## Incident and rollback

- Revoke a reviewer by setting `reviewers/{uid}.active` to `false` using an
  administrator path; never loosen Firestore rules for this.
- Disable the Cloud Run service or job rather than deleting Firestore evidence.
- Preserve `finance_runs` and `audit_events` for review. The workflow never
  mutates ledger totals after it has calculated a run.

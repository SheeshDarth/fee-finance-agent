# FeeOps Administrator Runbook

Target project: `intern-bnmit-july-2026`
Region: `us-central1`
Deployment platform: IAM-protected Cloud Run service; local React dashboard

> The administrator has selected the no-Firebase operating mode. This runbook's
> Firebase-specific sections are retained only as a legacy option. The active
> instructions are in [no-firebase-operating-mode.md](no-firebase-operating-mode.md).

## Security decisions

- The company project is the sole FeeOps target. Do not use `test1-457903`.
- Cloud Run and local tools use Application Default Credentials. No
  service-account JSON key is created, downloaded, mounted, or committed.
- The deployed service temporarily uses the default Compute runtime identity;
  replace it with `feeops-runtime@intern-bnmit-july-2026.iam.gserviceaccount.com`
  with Vertex AI User before a hardened deployment.
- No Firebase client configuration is used. `frontend/.env` remains absent.
- The local dashboard displays reproducible output; the private Cloud Run agent
  is invoked with a short-lived IAM identity token.

## One-time administrator work

1. Create the dedicated runtime service account and grant it `roles/aiplatform.user`.
2. Grant the deployer `roles/iam.serviceAccountUser` on that identity.
3. Attach the identity to the Cloud Run service and verify the ADK invocation.
4. Never provide a service-account key or a Gemini API key.

The active operating steps and Cloud Run invocation are centralized in
[no-firebase-operating-mode.md](no-firebase-operating-mode.md). The optional
Firebase reference remains in [company-cloud-deployment.md](company-cloud-deployment.md)
and must not be mixed with a personal Firebase project.

## Ongoing operation

1. Run the deterministic snapshot locally before the dashboard demo.
2. Invoke the Cloud Run agent using `backend/scripts/invoke_cloud_run_agent.ps1`.
3. Review payment exceptions and reminder drafts in the local dashboard.
4. Any outbound collection communication happens outside this prototype after
   human review; FeeOps never sends it automatically.

## Incident and rollback

- Remove an individual's `roles/run.invoker` binding if they should no longer
  invoke the private agent.
- Disable the Cloud Run service rather than deleting deployment evidence.
- Preserve versioned repository fixtures and run outputs for review. The
  workflow never mutates ledger totals after it has calculated a run.

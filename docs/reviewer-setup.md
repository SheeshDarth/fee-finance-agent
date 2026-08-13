# Reviewer Setup

Use this only after the Firebase Web App and Firestore database exist in the target project.

1. In Firebase Console, open the project and enable Authentication -> Sign-in method -> Email/Password.
2. Create a reviewer account using an evaluator-owned email address. Do not commit credentials to the repository.
3. Sign in once through the FeeOps dashboard.
4. In Firestore, create `reviewers/{the-auth-uid}` with:

```json
{
  "active": true,
  "displayName": "Accounts reviewer",
  "role": "reviewer"
}
```

5. Copy the target Firebase Web App config into ignored `frontend/.env` and run `npm run dev`.
6. Start `python firestore_worker.py`, sign in, click **Run live workflow**, and verify the run reaches `AWAITING_REVIEW`.

The Firestore rules require an authenticated active reviewer for run creation and reviewer actions. Passwords, API keys, service-account keys, and evaluator emails must remain outside Git.

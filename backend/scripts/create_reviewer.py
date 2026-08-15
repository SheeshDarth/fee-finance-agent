r"""Create a Firebase Auth reviewer and the required Firestore reviewer record.

Set FEEOPS_REVIEWER_EMAIL and FEEOPS_REVIEWER_PASSWORD in backend/.env before
running. Cloud Run uses its attached runtime service account; local execution
can use Application Default Credentials or an ignored company-project key.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT   = BACKEND_DIR.parent

def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(BACKEND_DIR / ".env")
        load_dotenv(REPO_ROOT / "frontend" / ".env")
    except ImportError:
        pass
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if creds and not os.path.isabs(creds):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((BACKEND_DIR / creds).resolve())

_load_env()

FIREBASE_API_KEY  = os.getenv("VITE_FIREBASE_API_KEY", "").strip()
GCP_PROJECT_ID    = os.getenv("GCP_PROJECT_ID", "").strip()
REVIEWER_EMAIL    = os.getenv("FEEOPS_REVIEWER_EMAIL", "").strip()
REVIEWER_PASSWORD = os.getenv("FEEOPS_REVIEWER_PASSWORD", "")

def identity_request(path: str, payload: dict[str, str]) -> dict[str, object]:
    request = Request(
        f"https://identitytoolkit.googleapis.com/v1/{path}?key={FIREBASE_API_KEY}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8")
        raise RuntimeError(body) from error


def create_firebase_user(email: str, password: str) -> str:
    if not FIREBASE_API_KEY:
        sys.exit("ERROR: VITE_FIREBASE_API_KEY not set. Load frontend/.env first.")
    try:
        body = identity_request("accounts:signUp", {"email": email, "password": password, "returnSecureToken": "true"})
    except RuntimeError as error:
        if "EMAIL_EXISTS" not in str(error):
            sys.exit(f"ERROR creating Firebase user: {error}")
        try:
            body = identity_request("accounts:signInWithPassword", {"email": email, "password": password, "returnSecureToken": "true"})
        except RuntimeError as sign_in_error:
            sys.exit(f"ERROR signing in existing reviewer: {sign_in_error}")
        uid = str(body["localId"])
        print(f"[~] Reviewer already exists: {email}  uid={uid}")
        return uid
    else:
        uid = str(body["localId"])
        print(f"[+] Created Firebase user: {email}  uid={uid}")
        return uid

def write_reviewer_doc(uid: str) -> None:
    import datetime
    from google.cloud import firestore

    db = firestore.Client(project=GCP_PROJECT_ID)
    db.collection("reviewers").document(uid).set({
        "email": REVIEWER_EMAIL,
        "role": "reviewer",
        "active": True,
        "createdAt": datetime.datetime.utcnow().isoformat() + "Z",
        "project": GCP_PROJECT_ID,
    })
    print(f"[+] Wrote reviewers/{uid} to Firestore project={GCP_PROJECT_ID}")

def main():
    if not GCP_PROJECT_ID:
        sys.exit("ERROR: GCP_PROJECT_ID must be set in backend/.env.")
    if not REVIEWER_EMAIL or not REVIEWER_PASSWORD:
        sys.exit("ERROR: Set FEEOPS_REVIEWER_EMAIL and FEEOPS_REVIEWER_PASSWORD in backend/.env.")
    print(f"FeeOps reviewer setup  --  project: {GCP_PROJECT_ID}")
    uid = create_firebase_user(REVIEWER_EMAIL, REVIEWER_PASSWORD)
    write_reviewer_doc(uid)
    print()
    print("=" * 60)
    print("Reviewer account ready!")
    print(f"  Email   : {REVIEWER_EMAIL}")
    print(f"  UID     : {uid}")
    print(f"  Firestore: reviewers/{uid}")
    print("=" * 60)

if __name__ == "__main__":
    main()

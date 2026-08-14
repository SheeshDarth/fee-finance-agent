r"""
create_reviewer.py  --  One-shot: create Firebase Auth reviewer account and write reviewers/{uid} to Firestore.

Usage (from repo root):
    $env:GOOGLE_APPLICATION_CREDENTIALS = "backend\service-account.json"
    .\backend\venv\Scripts\python.exe backend\scripts\create_reviewer.py
"""
from __future__ import annotations
import os, sys
from pathlib import Path
import requests

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
GCP_PROJECT_ID    = os.getenv("GCP_PROJECT_ID", "test1-457903").strip()
REVIEWER_EMAIL    = "reviewer@feeops.demo"
REVIEWER_PASSWORD = "FeeOps-Demo-2026!"

def create_firebase_user(email, password):
    if not FIREBASE_API_KEY:
        sys.exit("ERROR: VITE_FIREBASE_API_KEY not set. Load frontend/.env first.")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True}, timeout=15)
    body = resp.json()
    if resp.status_code == 200:
        uid = body["localId"]
        print(f"[+] Created Firebase user: {email}  uid={uid}")
        return uid
    if body.get("error", {}).get("message") == "EMAIL_EXISTS":
        url2 = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
        r2   = requests.post(url2, json={"email": email, "password": password, "returnSecureToken": True}, timeout=15)
        b2   = r2.json()
        if r2.status_code == 200:
            uid = b2["localId"]
            print(f"[~] User already exists: {email}  uid={uid}")
            return uid
        sys.exit(f"ERROR signing in existing user: {b2}")
    sys.exit(f"ERROR creating Firebase user: {body}")

def write_reviewer_doc(uid):
    try:
        import firebase_admin
        from firebase_admin import credentials as fb_creds, firestore as fb_fs
    except ImportError:
        sys.exit("ERROR: firebase-admin not installed. Run: pip install firebase-admin")
    import datetime
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not cred_path or not os.path.exists(cred_path):
        sys.exit(f"ERROR: GOOGLE_APPLICATION_CREDENTIALS not found at: {cred_path}")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(fb_creds.Certificate(cred_path))
    db = fb_fs.client()
    db.collection("reviewers").document(uid).set({
        "email": REVIEWER_EMAIL,
        "role": "reviewer",
        "createdAt": datetime.datetime.utcnow().isoformat() + "Z",
        "project": GCP_PROJECT_ID,
    })
    print(f"[+] Wrote reviewers/{uid} to Firestore project={GCP_PROJECT_ID}")

def main():
    print(f"FeeOps reviewer setup  --  project: {GCP_PROJECT_ID}")
    uid = create_firebase_user(REVIEWER_EMAIL, REVIEWER_PASSWORD)
    write_reviewer_doc(uid)
    print()
    print("=" * 60)
    print("Reviewer account ready!")
    print(f"  Email   : {REVIEWER_EMAIL}")
    print(f"  Password: {REVIEWER_PASSWORD}")
    print(f"  UID     : {uid}")
    print(f"  Firestore: reviewers/{uid}")
    print("=" * 60)

if __name__ == "__main__":
    main()

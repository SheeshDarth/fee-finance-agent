"""verify_firestore.py -- Check finance_runs and reviewers collections."""
from __future__ import annotations
import json, os, sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT   = BACKEND_DIR.parent

try:
    from dotenv import load_dotenv
    load_dotenv(BACKEND_DIR / ".env")
    load_dotenv(REPO_ROOT / "frontend" / ".env")
except ImportError:
    pass

creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
if creds and not os.path.isabs(creds):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((BACKEND_DIR / creds).resolve())

import firebase_admin
from firebase_admin import credentials, firestore

cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
if not cred_path or not os.path.exists(cred_path):
    sys.exit(f"ERROR: GOOGLE_APPLICATION_CREDENTIALS not found at: {cred_path}")

if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(cred_path))

db = firestore.client()

# Check finance_runs
runs = list(db.collection("finance_runs").limit(3).stream())
print(f"finance_runs count (up to 3): {len(runs)}")
for r in runs:
    d = r.to_dict()
    dash = json.dumps(d.get("dashboard", {}))[:120]
    print(f"  {r.id}: status={d.get('status')} asOf={d.get('asOf')} dashboard={dash}")

# Check reviewers
revs = list(db.collection("reviewers").stream())
print(f"reviewers count: {len(revs)}")
for rv in revs:
    print(f"  {rv.id}: {rv.to_dict()}")

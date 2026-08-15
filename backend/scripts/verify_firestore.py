"""verify_firestore.py -- Check finance_runs and reviewers collections with ADC."""
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

project_id = os.getenv("GCP_PROJECT_ID", "").strip()
if not project_id:
    sys.exit("ERROR: GCP_PROJECT_ID must be set. Use ADC locally or a Cloud Run runtime identity.")

from google.cloud import firestore

db = firestore.Client(project=project_id)

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

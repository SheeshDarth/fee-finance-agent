import {
  addDoc,
  collection,
  doc,
  onSnapshot,
  serverTimestamp,
} from "firebase/firestore";
import { db } from "./firebase";

const CHILD_COLLECTIONS = [
  "student_positions",
  "reconciliation_results",
  "collection_worklist",
  "reminder_drafts",
  "forecast_students",
  "leakage_findings",
  "agent_decisions",
  "escalations",
  "audit_events",
];

export async function createFinanceRun(asOf, customData = null) {
  if (!db) throw new Error("Firebase is not configured");
  const payload = {
    status: "PENDING",
    asOf,
    requestedAt: serverTimestamp(),
  };
  if (customData) {
    payload.customData = customData;
  }
  const run = await addDoc(collection(db, "finance_runs"), payload);
  return run.id;
}

export async function createReviewAction(runId, action) {
  if (!db) throw new Error("Firebase is not configured");
  return addDoc(collection(db, "finance_runs", runId, "review_actions"), {
    ...action,
    status: "PENDING",
    createdAt: serverTimestamp(),
  });
}

export function subscribeToRun(runId, onChange, onError) {
  if (!db || !runId) return () => {};
  const state = { dashboard: null };
  const unsubscribe = [];
  unsubscribe.push(onSnapshot(doc(db, "finance_runs", runId), (snapshot) => {
    if (!snapshot.exists()) return;
    Object.assign(state, snapshot.data());
    onChange({ ...state });
  }, onError));
  CHILD_COLLECTIONS.forEach((name) => {
    unsubscribe.push(onSnapshot(collection(db, "finance_runs", runId, name), (snapshot) => {
      state[name] = snapshot.docs.map((item) => ({ id: item.id, ...item.data() }));
      onChange({ ...state });
    }, onError));
  });
  return () => unsubscribe.forEach((stop) => stop());
}

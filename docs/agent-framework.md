# Agent Framework Choice

## Choice

This prototype uses a deterministic Python workflow orchestrator plus the Google Gen AI SDK through Vertex AI for bounded language generation. It does not use Google ADK 2.0.

## Justification

The assessment's highest-risk behavior is monetary correctness. The workflow has a fixed sequence, explicit state transitions, integer-paise calculations, trace IDs, confidence gates, and human-review boundaries. There is no benefit in allowing an autonomous model to choose tools or mutate financial state.

The Google Gen AI SDK is the equivalent framework boundary used here for the one task that benefits from an LLM: wording a reminder. Python remains authoritative for fee heads, instalments, concessions, waivers, payments, late fees, balances, ageing, plan compliance, worklist scores, and audit records.

## Agent Boundary

~~~mermaid
flowchart LR
  Facts["Deterministic ledger facts"] --> Prompt["Constrained Gemini prompt"]
  Prompt --> Model["Vertex AI Gemini"]
  Model --> Draft["Subject, tone, message"]
  Draft --> Guard["Exact amount and due-date validator"]
  Guard -->|pass| Review["Draft for human review"]
  Guard -->|fail| Fallback["Deterministic template"]
  Facts -. never model-authored .-> Ledger["Official ledger values"]
~~~

The model cannot write Firestore financial collections, approve payments, alter balances, or send reminders. This bounded design is intentionally safer than a general autonomous agent for a finance workflow.


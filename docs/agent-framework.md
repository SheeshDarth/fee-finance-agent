# Agent Framework Choice

## Choice

This prototype uses a deterministic Python workflow plus a real Google ADK 2.x wrapper at `backend/feeops_adk/agent.py`. The Google Gen AI SDK through Vertex AI remains the bounded wording integration in `llm_drafter.py`.

## Justification

The assessment's highest-risk behavior is monetary correctness. The workflow has a fixed sequence, explicit state transitions, integer-paise calculations, trace IDs, confidence gates, and human-review boundaries. There is no benefit in allowing an autonomous model to choose tools or mutate financial state.

ADK is the agent orchestration and conversational boundary. Its tools expose the trusted workflow as read-only operations. Python remains authoritative for fee heads, instalments, concessions, waivers, payments, late fees, balances, ageing, plan compliance, worklist scores, and audit records.

## Agent Boundary

~~~mermaid
flowchart LR
  ADK[Google ADK 2.x Agent Runtime] -->|read-only tool call| Facts
  Facts["Deterministic ledger facts"] --> Prompt["Constrained Gemini prompt"]
  Prompt --> Model["Vertex AI Gemini"]
  Model --> Draft["Subject, tone, message"]
  Draft --> Guard["Exact amount and due-date validator"]
  Guard -->|pass| Review["Draft for human review"]
  Guard -->|fail| Fallback["Deterministic template"]
  Facts -. never model-authored .-> Ledger["Official ledger values"]
~~~

The model cannot write Firestore financial collections, approve payments, alter balances, or send reminders. This bounded design is intentionally safer than a general autonomous agent for a finance workflow.

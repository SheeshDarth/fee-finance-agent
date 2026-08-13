# LLM Monetary Safety Note

The ledger is the authority. It calculates fee amounts, late fees, concessions, waivers, payments, ageing, plan compliance, and worklist scores in deterministic Python using integer paise.

When enabled, Gemini receives a small fact block containing the already-calculated reminder amount and due date. The model returns subject, message, and tone. It is not asked to calculate a balance. The validator extracts every \`Rs.\` amount from the message and requires the set to equal the one deterministic reminder amount. It also requires the exact due date to be present. Unknown or altered figures fail validation. A failed Gemini call or failed parse uses a deterministic template fallback and records its source in the output.

This boundary prevents an LLM from inventing a balance, changing a late fee, or sending a message automatically. Human review remains required for payment matches, reminder approval, and any future action that changes the official ledger.


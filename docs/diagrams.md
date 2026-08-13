# Project Diagrams

These diagrams are Mermaid source artifacts so they render in GitHub and remain editable.

Rendered PNG exports are included for the walkthrough and offline review:

- [Overall system architecture](assets/overall-system-architecture.png)
- [Finance run workflow](assets/finance-run-workflow.png)
- [Data relationship model](assets/data-relationship.png)
- [Live run and reviewer state](assets/live-run-reviewer-state.png)

## 1. System Architecture

~~~mermaid
flowchart LR
  subgraph Inputs["Source records"]
    S[Students]
    F[Fee heads and instalments]
    A[Concessions and waivers]
    P[Payments]
    H[Payment history]
    PP[Approved payment plans]
  end
  subgraph Engine["Python finance agent"]
    R[Reconciliation confidence gate]
    L[Integer-paise ledger]
    LF[Late-fee policy engine]
    PC[Plan compliance]
    WL[History-based worklist]
    D[Reminder drafter and validator]
    AU[Audit event writer]
  end
  subgraph Cloud["Google Cloud and Firebase"]
    FS[(Firestore finance_runs)]
    W[Firestore worker]
    AUTH[Firebase Authentication]
    UI[React live dashboard]
    G[Vertex AI Gemini]
  end
  S --> R
  F --> LF
  A --> L
  P --> R
  H --> WL
  PP --> PC
  R --> L
  LF --> L
  L --> PC
  PC --> WL
  L --> D
  D -. wording only .-> G
  G -. validated wording .-> D
  L --> AU
  D --> AU
  AU --> FS
  W --> FS
  FS --> UI
  AUTH --> UI
  UI -. reviewer action .-> FS
~~~

## 2. Finance Run Workflow

~~~mermaid
flowchart TD
  Start([Run requested]) --> Ingest[Load source JSON or Firestore input]
  Ingest --> Match[Reconcile each payment]
  Match --> Gate{Confidence?}
  Gate -->|CONFIDENT| Apply[Apply payment FIFO]
  Gate -->|POSSIBLE or NEEDS_REVIEW| Hold[Exclude from verified ledger]
  Apply --> Fees[Calculate late fee by policy and grace period]
  Hold --> Fees
  Fees --> Adjust[Apply concession and waiver FIFO]
  Adjust --> Position[Build student position]
  Position --> Plan[Evaluate each plan installment]
  Plan --> Score[Score collection worklist with history]
  Score --> Draft[Draft reminders for overdue families without approved plans]
  Draft --> Validate{Exact money and due-date validation}
  Validate -->|Pass| Audit[Write audit events]
  Validate -->|Fail| Fallback[Use deterministic fallback and audit reason]
  Fallback --> Audit
  Audit --> Publish[Write local output or Firestore run]
  Publish --> End([Complete or awaiting review])
~~~

## 3. Data Relationships

~~~mermaid
erDiagram
  STUDENT ||--o{ FEE_ITEM : billed
  STUDENT ||--o{ CONCESSION : receives
  STUDENT ||--o{ WAIVER : receives
  STUDENT ||--o{ PAYMENT : identified_by
  STUDENT ||--o{ PAYMENT_HISTORY : has
  STUDENT ||--o{ PAYMENT_PLAN : approved_for
  PAYMENT_PLAN ||--|{ PLAN_INSTALLMENT : contains
  PLAN_INSTALLMENT }o--o{ PAYMENT : references
  FEE_ITEM }o--o{ PAYMENT : allocated_from
  STUDENT {
    string studentId PK
    string name
    string class
    string guardianName
  }
  FEE_ITEM {
    string feeItemId PK
    string studentId FK
    string feeHead
    string term
    string instalmentId
    int amountPaise
    date dueDate
  }
  PAYMENT {
    string paymentId PK
    int amountPaise
    string mode
    date date
    string rawNarration
  }
  PAYMENT_PLAN {
    string planId PK
    string studentId FK
    string status
    string approvedBy
    date approvedAt
  }
~~~

## 4. Live Run and Reviewer State

~~~mermaid
stateDiagram-v2
  [*] --> PENDING: reviewer creates finance_run
  PENDING --> RUNNING: worker claims run
  RUNNING --> AWAITING_REVIEW: ambiguity or drafts exist
  RUNNING --> COMPLETE: no review items
  RUNNING --> FAILED: processing error
  AWAITING_REVIEW --> AWAITING_REVIEW: reviewer action recorded
  AWAITING_REVIEW --> COMPLETE: worker applies decision and re-runs ledger
  COMPLETE --> [*]
  FAILED --> [*]
~~~

The current prototype records reviewer actions and audit events. A production extension should re-run the immutable ledger after an approved match or reminder decision, which is documented as a limitation.

import React, { useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, ClipboardList, IndianRupee, ShieldCheck } from "lucide-react";
import data from "./demo-output.json";


function money(value) {
  return value || "Rs. 0";
}

function Stat({ label, value, icon: Icon }) {
  return (
    <section className="stat">
      <div className="statIcon"><Icon size={20} /></div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
    </section>
  );
}

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const reviewCount = useMemo(
    () => data.reconciliationResults.filter((item) => item.requiresHumanReview).length,
    []
  );

  return (
    <main>
      <header className="topbar">
        <div>
          <h1>Fee Collection & Finance Agent</h1>
          <p>Deterministic school-fee ledger with reconciliation review, collection priority, and dry-run reminder drafts.</p>
        </div>
        <div className="statusPill"><CheckCircle2 size={18} /> {data.status}</div>
      </header>

      <nav className="tabs" aria-label="Dashboard sections">
        {["dashboard", "reconciliation", "worklist", "reminders", "audit"].map((item) => (
          <button key={item} className={tab === item ? "active" : ""} onClick={() => setTab(item)}>
            {item}
          </button>
        ))}
      </nav>

      {tab === "dashboard" && (
        <>
          <section className="statsGrid">
            <Stat label="Net Due" value={money(data.dashboard.totalNetDue)} icon={IndianRupee} />
            <Stat label="Collected" value={money(data.dashboard.totalCollected)} icon={CheckCircle2} />
            <Stat label="Outstanding" value={money(data.dashboard.totalOutstanding)} icon={ClipboardList} />
            <Stat label="Overdue" value={money(data.dashboard.totalOverdue)} icon={AlertTriangle} />
          </section>

          <section className="split">
            <div>
              <h2>Ageing Buckets</h2>
              <table>
                <tbody>
                  {Object.entries(data.dashboard.ageingBuckets).map(([bucket, row]) => (
                    <tr key={bucket}><td>{bucket}</td><td>{row.amount}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div>
              <h2>Class Breakdown</h2>
              <table>
                <thead><tr><th>Class</th><th>Net Due</th><th>Collected</th><th>Overdue</th></tr></thead>
                <tbody>
                  {Object.entries(data.dashboard.byClass).map(([klass, row]) => (
                    <tr key={klass}><td>{klass}</td><td>{row.netDue}</td><td>{row.collected}</td><td>{row.overdue}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {tab === "reconciliation" && (
        <section>
          <h2>Payment Reconciliation <span className="muted">{reviewCount} need review</span></h2>
          <table>
            <thead><tr><th>Payment</th><th>Amount</th><th>Mode</th><th>Match</th><th>Confidence</th><th>Reason</th></tr></thead>
            <tbody>
              {data.reconciliationResults.map((item) => (
                <tr key={item.paymentId} className={item.requiresHumanReview ? "warnRow" : ""}>
                  <td>{item.paymentId}</td>
                  <td>Rs. {(item.amountPaise / 100).toLocaleString("en-IN")}</td>
                  <td>{item.mode}</td>
                  <td>{item.matchedStudentId || "Unmatched"}</td>
                  <td>{item.confidence}</td>
                  <td>{item.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === "worklist" && (
        <section>
          <h2>Prioritized Collection Worklist</h2>
          <div className="cards">
            {data.collectionWorklist.map((row) => (
              <article key={row.studentId} className="item">
                <div><strong>#{row.rank} {row.studentName}</strong><span>{row.class}</span></div>
                <p>{row.reason}</p>
                <footer>{row.shouldContact ? "Contact now" : "Do not contact"} · {row.outstanding}</footer>
              </article>
            ))}
          </div>
        </section>
      )}

      {tab === "reminders" && (
        <section>
          <h2>Reminder Drafts <span className="muted">review only, not sent</span></h2>
          <div className="cards">
            {data.reminderDrafts.map((draft) => (
              <article key={draft.studentId} className="item">
                <div><strong>{draft.studentName}</strong><span>{draft.tone}</span></div>
                <p>{draft.message}</p>
                <footer><ShieldCheck size={16} /> {draft.validationNote}</footer>
              </article>
            ))}
          </div>
        </section>
      )}

      {tab === "audit" && (
        <section>
          <h2>Audit Trail</h2>
          <table>
            <thead><tr><th>Time</th><th>Event</th><th>Actor</th></tr></thead>
            <tbody>
              {data.auditEvents.map((event, index) => (
                <tr key={`${event.eventType}-${index}`}>
                  <td>{new Date(event.timestamp).toLocaleString()}</td>
                  <td>{event.eventType}</td>
                  <td>{event.actor}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  );
}

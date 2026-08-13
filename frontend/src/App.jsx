import React, { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowUpRight,
  BadgeIndianRupee,
  CheckCircle2,
  ClipboardCheck,
  Clock3,
  FileClock,
  FileText,
  Landmark,
  LayoutDashboard,
  ListChecks,
  MessageSquareText,
  RefreshCcw,
  Search,
  ShieldCheck,
  Users,
} from "lucide-react";
import data from "./demo-output.json";

const TAB_ITEMS = [
  { id: "dashboard", label: "Overview", icon: LayoutDashboard },
  { id: "reconciliation", label: "Payment review", icon: RefreshCcw },
  { id: "worklist", label: "Collection worklist", icon: ListChecks },
  { id: "reminders", label: "Reminder drafts", icon: MessageSquareText },
  { id: "audit", label: "Audit trail", icon: FileClock },
];

const BUCKET_ORDER = ["0-30", "31-60", "60+"];

function money(value) {
  return value || "Rs. 0";
}

function formatDate(value) {
  return new Date(`${value}T00:00:00`).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function StatusBadge({ children, tone = "neutral" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function StatCard({ label, value, note, icon: Icon, tone = "neutral" }) {
  return (
    <article className={`statCard stat-${tone}`}>
      <div className="statCardTop">
        <span className="statIcon"><Icon size={18} strokeWidth={2.2} /></span>
        <span className="statLabel">{label}</span>
      </div>
      <strong>{value}</strong>
      <span className="statNote">{note}</span>
    </article>
  );
}

function SectionHeader({ eyebrow, title, detail, action }) {
  return (
    <div className="sectionHeader">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2>{title}</h2>
        {detail && <p className="sectionDetail">{detail}</p>}
      </div>
      {action}
    </div>
  );
}

function EmptyState({ icon: Icon = CheckCircle2, title, detail }) {
  return (
    <div className="emptyState">
      <Icon size={22} />
      <strong>{title}</strong>
      <span>{detail}</span>
    </div>
  );
}

function App() {
  const [tab, setTab] = useState("dashboard");
  const [search, setSearch] = useState("");
  const dashboard = data.dashboard;
  const reviewPayments = useMemo(
    () => data.reconciliationResults.filter((item) => item.requiresHumanReview),
    []
  );
  const overdueFamilies = useMemo(
    () => data.studentPositions.filter((item) => item.overduePaise > 0),
    []
  );
  const contactableFamilies = useMemo(
    () => data.collectionWorklist.filter((item) => item.shouldContact),
    []
  );
  const visibleWorklist = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return data.collectionWorklist;
    return data.collectionWorklist.filter((row) =>
      `${row.studentName} ${row.studentId} ${row.class} ${row.ageingBucket}`.toLowerCase().includes(query)
    );
  }, [search]);

  const selectTab = (nextTab) => {
    setTab(nextTab);
    setSearch("");
  };

  return (
    <div className="appShell">
      <aside className="sidebar">
        <div className="brandBlock">
          <div className="brandMark"><Landmark size={19} /></div>
          <div>
            <strong>FeeOps</strong>
            <span>Finance workspace</span>
          </div>
        </div>
        <div className="sidebarRule" />
        <p className="navLabel">Workspace</p>
        <nav className="sideNav" aria-label="Finance workspace sections">
          {TAB_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              type="button"
              key={id}
              className={tab === id ? "navItem active" : "navItem"}
              onClick={() => selectTab(id)}
              aria-current={tab === id ? "page" : undefined}
            >
              <Icon size={17} />
              <span>{label}</span>
              {id === "reconciliation" && reviewPayments.length > 0 && (
                <b>{reviewPayments.length}</b>
              )}
              {id === "reminders" && data.reminderDrafts.length > 0 && (
                <b>{data.reminderDrafts.length}</b>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebarBottom">
          <div className="trustNote">
            <ShieldCheck size={16} />
            <div>
              <strong>Money protected</strong>
              <span>Deterministic paise ledger</span>
            </div>
          </div>
          <p className="sidebarFoot">Local demo snapshot</p>
        </div>
      </aside>

      <main className="mainContent">
        <header className="pageHeader">
          <div>
            <p className="eyebrow">Accounts office / finance run</p>
            <h1>{TAB_ITEMS.find((item) => item.id === tab)?.label}</h1>
            <p className="pageSubtitle">School fee collection and reconciliation workspace</p>
          </div>
          <div className="runMeta">
            <StatusBadge tone="success"><CheckCircle2 size={13} /> Snapshot generated</StatusBadge>
            <span>As of {formatDate(data.asOf)}</span>
          </div>
        </header>

        {tab === "dashboard" && (
          <>
            <section className="attentionStrip" aria-label="Items needing attention">
              <div className="attentionLead">
                <span className="attentionIcon"><AlertTriangle size={19} /></span>
                <div>
                  <p className="eyebrow">Today&apos;s attention</p>
                  <h2>{reviewPayments.length + contactableFamilies.length} items need review or follow-up</h2>
                </div>
              </div>
              <div className="attentionItems">
                <button type="button" onClick={() => selectTab("reconciliation")}>
                  <strong>{reviewPayments.length}</strong>
                  <span>payments to review</span>
                  <ArrowUpRight size={14} />
                </button>
                <button type="button" onClick={() => selectTab("worklist")}>
                  <strong>{contactableFamilies.length}</strong>
                  <span>families to contact</span>
                  <ArrowUpRight size={14} />
                </button>
                <button type="button" onClick={() => selectTab("reminders")}>
                  <strong>{data.reminderDrafts.length}</strong>
                  <span>drafts awaiting review</span>
                  <ArrowUpRight size={14} />
                </button>
              </div>
            </section>

            <section className="statsGrid" aria-label="Finance summary">
              <StatCard label="Net due" value={money(dashboard.totalNetDue)} note="After concessions and waivers" icon={BadgeIndianRupee} />
              <StatCard label="Verified collected" value={money(dashboard.totalCollected)} note="Confirmed payments only" icon={CheckCircle2} tone="success" />
              <StatCard label="Outstanding" value={money(dashboard.totalOutstanding)} note={`${overdueFamilies.length} families with balance`} icon={ClipboardCheck} tone="warning" />
              <StatCard label="Overdue" value={money(dashboard.totalOverdue)} note="Past due date, unpaid" icon={Clock3} tone="danger" />
            </section>

            <section className="panel compactCallout">
              <div className="calloutIcon"><ShieldCheck size={18} /></div>
              <div>
                <strong>Verified ledger view</strong>
                <p>Amounts below exclude payments that still need human confirmation. Pending review: <b>{money(dashboard.pendingReview)}</b>.</p>
              </div>
              <button type="button" className="textButton" onClick={() => selectTab("reconciliation")}>Review payments <ArrowUpRight size={14} /></button>
            </section>

            <div className="dashboardGrid">
              <section className="panel">
                <SectionHeader eyebrow="Ageing" title="Overdue exposure" detail="Verified overdue balance by time outstanding" />
                <div className="ageingList">
                  {BUCKET_ORDER.map((bucket) => {
                    const row = dashboard.ageingBuckets[bucket];
                    const amount = row?.amountPaise || 0;
                    const total = dashboard.totalOverduePaise || 1;
                    return (
                      <div className="ageingRow" key={bucket}>
                        <div className="ageingLabel"><span className={`bucketDot bucket-${bucket.replace("+", "plus").replace("-", "")}`} /><strong>{bucket} days</strong><span>{Math.round((amount / total) * 100)}%</span></div>
                        <div className="progressTrack"><span style={{ width: `${Math.max((amount / total) * 100, amount ? 4 : 0)}%` }} /></div>
                        <strong className="ageingAmount">{row?.amount || "Rs. 0"}</strong>
                      </div>
                    );
                  })}
                </div>
              </section>

              <section className="panel">
                <SectionHeader eyebrow="By class" title="Class exposure" detail="Net due, verified collections, and overdue balance" />
                <div className="tableWrap">
                  <table>
                    <thead><tr><th>Class</th><th>Net due</th><th>Collected</th><th>Overdue</th></tr></thead>
                    <tbody>{Object.entries(dashboard.byClass).map(([klass, row]) => (
                      <tr key={klass}><td><strong>{klass}</strong></td><td>{row.netDue}</td><td className="positiveText">{row.collected}</td><td className={row.overduePaise ? "dangerText" : "mutedText"}>{row.overdue}</td></tr>
                    ))}</tbody>
                  </table>
                </div>
              </section>
            </div>

            <section className="panel">
              <SectionHeader eyebrow="By fee head" title="Fee-head exposure" detail="The ledger breaks every fee head into due, collected, outstanding, and overdue." />
              <div className="tableWrap">
                <table>
                  <thead><tr><th>Fee head</th><th>Items</th><th>Net due</th><th>Collected</th><th>Outstanding</th><th>Overdue</th></tr></thead>
                  <tbody>{Object.entries(dashboard.byFeeHead).map(([head, row]) => (
                    <tr key={head}><td><strong className="capitalize">{head}</strong></td><td>{row.count}</td><td>{row.netDue}</td><td className="positiveText">{row.collected}</td><td>{row.outstanding}</td><td className={row.overduePaise ? "dangerText" : "mutedText"}>{row.overdue}</td></tr>
                  ))}</tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {tab === "reconciliation" && (
          <section className="panel">
            <SectionHeader eyebrow="Control queue" title="Payment reconciliation" detail="Ambiguous payments stay outside the verified ledger until a human confirms them." action={<StatusBadge tone="warning"><AlertTriangle size={13} /> {reviewPayments.length} need review</StatusBadge>} />
            <div className="reviewBanner"><AlertTriangle size={17} /><span><strong>{money(dashboard.pendingReview)}</strong> is pending confirmation and excluded from official collections.</span></div>
            <div className="tableWrap">
              <table className="reconciliationTable">
                <thead><tr><th>Payment</th><th>Amount</th><th>Received</th><th>Match</th><th>Evidence / reason</th><th>Ledger treatment</th></tr></thead>
                <tbody>{data.reconciliationResults.map((item) => {
                  const isReview = item.requiresHumanReview;
                  const tone = item.confidence === "CONFIDENT" ? "success" : item.confidence === "POSSIBLE" ? "warning" : "danger";
                  return <tr key={item.paymentId} className={isReview ? "reviewRow" : ""}>
                    <td><strong>{item.paymentId}</strong><span className="cellSub">{item.mode}</span></td>
                    <td><strong>{money(`Rs. ${(item.amountPaise / 100).toLocaleString("en-IN")}`)}</strong></td>
                    <td>{formatDate(item.date)}</td>
                    <td>{item.matchedStudentId || <span className="mutedText">Unmatched</span>}<span className="cellSub"><StatusBadge tone={tone}>{item.confidence}</StatusBadge></span></td>
                    <td className="reasonCell">{item.reason}</td>
                    <td>{isReview ? <StatusBadge tone="warning">Excluded / review</StatusBadge> : <StatusBadge tone="success">Posted to ledger</StatusBadge>}</td>
                  </tr>;
                })}</tbody>
              </table>
            </div>
          </section>
        )}

        {tab === "worklist" && (
          <section className="panel">
            <SectionHeader eyebrow="Collections" title="Prioritized collection worklist" detail="Ranked by overdue age and outstanding amount. Approved payment plans are visible but not contacted." action={<label className="searchBox"><Search size={16} /><input aria-label="Search worklist" placeholder="Search family or class" value={search} onChange={(event) => setSearch(event.target.value)} /></label>} />
            <div className="worklistSummary"><span><strong>{visibleWorklist.length}</strong> families shown</span><span><strong>{contactableFamilies.length}</strong> contact now</span><span><strong>{data.collectionWorklist.filter((row) => row.hasApprovedPaymentPlan).length}</strong> on approved plan</span></div>
            <div className="tableWrap">
              <table>
                <thead><tr><th>Rank</th><th>Family</th><th>Class</th><th>Balance</th><th>Ageing</th><th>Reason</th><th>Action</th></tr></thead>
                <tbody>{visibleWorklist.map((row) => <tr key={row.studentId}>
                  <td><span className="rank">{row.rank}</span></td>
                  <td><strong>{row.studentName}</strong><span className="cellSub">{row.studentId}</span></td>
                  <td>{row.class}</td>
                  <td><strong>{row.outstanding}</strong><span className="cellSub">{row.daysOverdue ? `${row.daysOverdue} days overdue` : "Not overdue"}</span></td>
                  <td><StatusBadge tone={row.ageingBucket === "60+" ? "danger" : row.ageingBucket === "NOT_OVERDUE" ? "neutral" : "warning"}>{row.ageingBucket}</StatusBadge></td>
                  <td className="reasonCell">{row.reason}</td>
                  <td>{row.shouldContact ? <StatusBadge tone="danger">Contact now</StatusBadge> : <StatusBadge tone="neutral">Plan on file</StatusBadge>}</td>
                </tr>)}</tbody>
              </table>
            </div>
          </section>
        )}

        {tab === "reminders" && (
          <section className="panel">
            <SectionHeader eyebrow="Human review required" title="Reminder drafts" detail="Messages are deterministic templates for accounts-office review. Nothing is sent." action={<StatusBadge tone="neutral"><FileText size={13} /> Draft only</StatusBadge>} />
            <div className="reviewBanner neutralBanner"><ShieldCheck size={17} /><span>Amounts come from the verified ledger and are checked before a draft is displayed.</span></div>
            <div className="draftGrid">
              {data.reminderDrafts.map((draft) => <article className="draftCard" key={draft.studentId}>
                <div className="draftTop"><div><strong>{draft.studentName}</strong><span>{draft.guardianName}</span></div><StatusBadge tone={draft.ageingBucket === "31-60" ? "warning" : "neutral"}>{draft.ageingBucket}</StatusBadge></div>
                <div className="draftMeta"><span>{draft.tone}</span><strong>{draft.ageingBucket === "31-60" ? "Firm" : "Polite"} tone</strong></div>
                <p className="draftMessage">{draft.message}</p>
                <div className="draftFooter"><StatusBadge tone="success"><CheckCircle2 size={12} /> {draft.validationNote}</StatusBadge><span>Not sent</span></div>
              </article>)}
            </div>
            {data.reminderDrafts.length === 0 && <EmptyState icon={MessageSquareText} title="No drafts" detail="No eligible overdue family needs a reminder draft." />}
          </section>
        )}

        {tab === "audit" && (
          <section className="panel">
            <SectionHeader eyebrow="Traceability" title="Audit trail" detail="Every run, reconciliation decision, student position, and draft is timestamped." action={<StatusBadge tone="success"><ShieldCheck size={13} /> {data.auditEvents.length} events</StatusBadge>} />
            <div className="auditList">
              {data.auditEvents.map((event, index) => <article className="auditRow" key={`${event.eventType}-${index}`}>
                <span className={`auditDot ${event.eventType.includes("REVIEW") ? "auditWarn" : event.eventType.includes("COMPLETED") ? "auditSuccess" : ""}`} />
                <div className="auditMain"><strong>{event.eventType.replaceAll("_", " ")}</strong><span>{event.actor}</span></div>
                <time>{new Date(event.timestamp).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</time>
              </article>)}
            </div>
          </section>
        )}

        <footer className="pageFooter"><span><ShieldCheck size={14} /> Figures are deterministic and traceable to source records.</span><span>Local JSON demo / Firestore write optional</span></footer>
      </main>
    </div>
  );
}

export default App;

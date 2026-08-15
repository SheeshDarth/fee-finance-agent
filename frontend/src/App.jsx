import React, { useEffect, useMemo, useState, useRef } from "react";
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
  ShieldAlert,
  TrendingUp,
  Upload,
  Users,
} from "lucide-react";
import * as XLSX from "xlsx";
import { onAuthStateChanged, signInWithEmailAndPassword, signOut } from "firebase/auth";
import data from "./demo-output.json";
import { auth, isFirebaseConfigured } from "./firebase";
import { createFinanceRun, createReviewAction, subscribeToRun } from "./liveData";

const TAB_ITEMS = [
  { id: "dashboard", label: "Overview", icon: LayoutDashboard },
  { id: "reconciliation", label: "Payment review", icon: RefreshCcw },
  { id: "worklist", label: "Collection worklist", icon: ListChecks },
  { id: "reminders", label: "Reminder drafts", icon: MessageSquareText },
  { id: "insights", label: "Forecast & controls", icon: TrendingUp },
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

function LiveAuth({ user, email, password, setEmail, setPassword, onSignIn, onSignOut, authMessage }) {
  if (!isFirebaseConfigured) return <StatusBadge tone="neutral"><Landmark size={13} /> Local demo mode</StatusBadge>;
  if (user) return <div className="authInline"><StatusBadge tone="success"><CheckCircle2 size={13} /> Reviewer signed in</StatusBadge><button type="button" className="quietButton" onClick={onSignOut}>Sign out</button></div>;
  return <form className="authInline" onSubmit={onSignIn} aria-label="Reviewer sign in">
    <input aria-label="Reviewer email" type="email" placeholder="Reviewer email" value={email} onChange={(event) => setEmail(event.target.value)} required />
    <input aria-label="Reviewer password" type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} required />
    <button type="submit" className="quietButton">Sign in</button>
    {authMessage && <span className="authMessage">{authMessage}</span>}
  </form>;
}

function App() {
  const [tab, setTab] = useState("dashboard");
  const [search, setSearch] = useState("");
  const [activeData, setActiveData] = useState(data);
  const [liveRunId, setLiveRunId] = useState(null);
  const [liveStatus, setLiveStatus] = useState(null);
  const [liveError, setLiveError] = useState("");
  const [user, setUser] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);
  const dashboard = activeData.dashboard;
  const forecast = activeData.forecast || { summary: {}, studentForecasts: [] };
  const leakage = activeData.leakage || { summary: {}, findings: [] };
  useEffect(() => (auth ? onAuthStateChanged(auth, setUser) : undefined), []);
  useEffect(() => {
    if (!liveRunId) return undefined;
    return subscribeToRun(liveRunId, (snapshot) => {
      setLiveStatus(snapshot.status || "RUNNING");
      setActiveData((current) => {
        const nextForecast = snapshot.forecast
          ? { ...current.forecast, summary: snapshot.forecast }
          : current.forecast;
        const nextLeakage = snapshot.leakageSummary || snapshot.leakage_findings
          ? {
              ...current.leakage,
              summary: snapshot.leakageSummary || current.leakage?.summary,
              findings: snapshot.leakage_findings || current.leakage?.findings,
            }
          : current.leakage;
        return {
          ...current,
          ...snapshot,
          dashboard: snapshot.dashboard || current.dashboard,
          studentPositions: snapshot.student_positions || current.studentPositions,
          reconciliationResults: snapshot.reconciliation_results || current.reconciliationResults,
          collectionWorklist: snapshot.collection_worklist || current.collectionWorklist,
          reminderDrafts: snapshot.reminder_drafts || current.reminderDrafts,
          forecast: { ...nextForecast, studentForecasts: snapshot.forecast_students || nextForecast?.studentForecasts || [] },
          leakage: nextLeakage,
          agentDecisions: snapshot.agent_decisions || current.agentDecisions,
          escalations: snapshot.escalations || current.escalations,
          auditEvents: snapshot.audit_events || current.auditEvents,
        };
      });
    }, (error) => setLiveError(error.message));
  }, [liveRunId]);
  const reviewPayments = useMemo(
    () => activeData.reconciliationResults.filter((item) => item.requiresHumanReview), [activeData]
  );
  const overdueFamilies = useMemo(
    () => activeData.studentPositions.filter((item) => item.overduePaise > 0), [activeData]
  );
  const contactableFamilies = useMemo(
    () => activeData.collectionWorklist.filter((item) => item.shouldContact), [activeData]
  );
  const decisionsByStudent = useMemo(
    () => new Map((activeData.agentDecisions || []).map((decision) => [decision.studentId, decision])), [activeData]
  );
  const highLeakageFindings = useMemo(
    () => (leakage.findings || []).filter((item) => item.severity === "HIGH"), [leakage]
  );
  const visibleWorklist = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return activeData.collectionWorklist;
    return activeData.collectionWorklist.filter((row) =>
      `${row.studentName} ${row.studentId} ${row.class} ${row.ageingBucket}`.toLowerCase().includes(query)
    );
  }, [activeData, search]);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    setIsUploading(true);
    setLiveError("");
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: "array" });
        const customData = {};
        workbook.SheetNames.forEach((sheet) => {
          customData[sheet] = XLSX.utils.sheet_to_json(workbook.Sheets[sheet]);
        });
        const runId = await createFinanceRun(activeData.asOf, customData);
        setLiveRunId(runId);
        setLiveStatus("PENDING");
      } catch (error) {
        setLiveError("Failed to parse Excel file: " + error.message);
      } finally {
        setIsUploading(false);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    };
    reader.readAsArrayBuffer(file);
  };

  const requestLiveRun = async () => {
    try {
      const runId = await createFinanceRun(activeData.asOf);
      setLiveRunId(runId);
      setLiveStatus("PENDING");
      setLiveError("");
    } catch (error) { setLiveError(error.message); }
  };
  const signIn = async (event) => {
    event.preventDefault();
    try { await signInWithEmailAndPassword(auth, email, password); setPassword(""); setAuthMessage(""); }
    catch (error) { setAuthMessage(error.message); }
  };
  const submitReviewAction = async (targetType, targetId, decision) => {
    if (!liveRunId || !user) return;
    try { await createReviewAction(liveRunId, { targetType, targetId, decision, reviewerUid: user.uid }); setLiveError(""); }
    catch (error) { setLiveError(error.message); }
  };

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
              {id === "reminders" && activeData.reminderDrafts.length > 0 && (
                <b>{activeData.reminderDrafts.length}</b>
              )}
              {id === "insights" && highLeakageFindings.length > 0 && (
                <b>{highLeakageFindings.length}</b>
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
          <p className="sidebarFoot">{liveRunId ? `Live run ${liveRunId.slice(0, 7)}` : "Local demo snapshot"}</p>
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
            <LiveAuth user={user} email={email} password={password} setEmail={setEmail} setPassword={setPassword} onSignIn={signIn} onSignOut={() => signOut(auth)} authMessage={authMessage} />
            <a href="/template.xlsx" download className="runButton" style={{textDecoration: "none", color: "inherit", border: "1px solid var(--border)", padding: "0 10px"}}><FileText size={14} /> Download Template</a>
            <input type="file" accept=".xlsx" style={{ display: "none" }} ref={fileInputRef} onChange={handleFileUpload} />
            <button type="button" className="runButton" onClick={() => fileInputRef.current?.click()} disabled={!isFirebaseConfigured || !user || isUploading}><Upload size={14} /> {isUploading ? "Uploading..." : "Upload Excel"}</button>
            <button type="button" className="runButton" onClick={requestLiveRun} disabled={!isFirebaseConfigured || !user}><ArrowUpRight size={14} /> Run live workflow</button>
            <StatusBadge tone={liveRunId ? "success" : "neutral"}><CheckCircle2 size={13} /> {liveRunId ? `Live ${liveStatus || "connecting"}` : "Snapshot generated"}</StatusBadge>
            <span>As of {formatDate(activeData.asOf)}</span>
          </div>
        </header>
        {liveError && <div className="errorBanner" role="alert"><AlertTriangle size={16} />{liveError}</div>}

        {tab === "dashboard" && (
          <>
            <section className="attentionStrip" aria-label="Items needing attention">
              <div className="attentionLead">
                <span className="attentionIcon"><AlertTriangle size={19} /></span>
                <div>
                  <p className="eyebrow">Today&apos;s attention</p>
                  <h2>{reviewPayments.length + contactableFamilies.length + highLeakageFindings.length} items need review or follow-up</h2>
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
                  <strong>{activeData.reminderDrafts.length}</strong>
                  <span>drafts awaiting review</span>
                  <ArrowUpRight size={14} />
                </button>
                <button type="button" onClick={() => selectTab("insights")}>
                  <strong>{highLeakageFindings.length}</strong>
                  <span>control exceptions</span>
                  <ArrowUpRight size={14} />
                </button>
              </div>
            </section>

            <section className="statsGrid" aria-label="Finance summary">
              <StatCard label="Net due" value={money(dashboard.totalNetDue)} note="After concessions and waivers" icon={BadgeIndianRupee} />
              <StatCard label="Verified collected" value={money(dashboard.totalCollected)} note="Confirmed payments only" icon={CheckCircle2} tone="success" />
              <StatCard label="Outstanding" value={money(dashboard.totalOutstanding)} note={`${overdueFamilies.length} families with balance`} icon={ClipboardCheck} tone="warning" />
              <StatCard label="Overdue" value={money(dashboard.totalOverdue)} note="Past due date, unpaid" icon={Clock3} tone="danger" />
              <StatCard label="Late fees" value={money(dashboard.totalLateFee)} note="Policy-derived charges" icon={BadgeIndianRupee} tone="warning" />
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
                  <thead><tr><th>Fee head</th><th>Items</th><th>Net due</th><th>Collected</th><th>Outstanding</th><th>Overdue</th><th>Late fee</th></tr></thead>
                  <tbody>{Object.entries(dashboard.byFeeHead).map(([head, row]) => (
                    <tr key={head}><td><strong className="capitalize">{head}</strong></td><td>{row.count}</td><td>{row.netDue}</td><td className="positiveText">{row.collected}</td><td>{row.outstanding}</td><td className={row.overduePaise ? "dangerText" : "mutedText"}>{row.overdue}</td><td>{row.lateFee}</td></tr>
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
                <tbody>{activeData.reconciliationResults.map((item) => {
                  const isReview = item.requiresHumanReview;
                  const tone = item.confidence === "CONFIDENT" ? "success" : item.confidence === "POSSIBLE" ? "warning" : "danger";
                  return <tr key={item.paymentId} className={isReview ? "reviewRow" : ""}>
                    <td><strong>{item.paymentId}</strong><span className="cellSub">{item.mode}</span></td>
                    <td><strong>{money(`Rs. ${(item.amountPaise / 100).toLocaleString("en-IN")}`)}</strong></td>
                    <td>{formatDate(item.date)}</td>
                    <td>{item.matchedStudentId || <span className="mutedText">Unmatched</span>}<span className="cellSub"><StatusBadge tone={tone}>{item.confidence}</StatusBadge></span></td>
                    <td className="reasonCell">{item.reason}</td>
                    <td>{isReview ? <>{liveRunId && user ? <button type="button" className="smallAction" onClick={() => submitReviewAction("PAYMENT", item.paymentId, item.matchedStudentId ? "CONFIRM_MATCH" : "MARK_REVIEWED")}>Record reviewer action</button> : <StatusBadge tone="warning">Excluded / review</StatusBadge>}</> : <StatusBadge tone="success">Posted to ledger</StatusBadge>}</td>
                  </tr>;
                })}</tbody>
              </table>
            </div>
          </section>
        )}

        {tab === "worklist" && (
          <section className="panel">
            <SectionHeader eyebrow="Collections" title="Prioritized collection worklist" detail="Ranked by overdue age and outstanding amount. Approved payment plans are visible but not contacted." action={<label className="searchBox"><Search size={16} /><input aria-label="Search worklist" placeholder="Search family or class" value={search} onChange={(event) => setSearch(event.target.value)} /></label>} />
            <div className="worklistSummary"><span><strong>{visibleWorklist.length}</strong> families shown</span><span><strong>{contactableFamilies.length}</strong> contact now</span><span><strong>{activeData.escalations?.length || 0}</strong> cases escalated</span><span><strong>{activeData.collectionWorklist.filter((row) => row.hasApprovedPaymentPlan).length}</strong> on approved plan</span></div>
            <div className="tableWrap">
              <table>
                <thead><tr><th>Rank</th><th>Family</th><th>Class</th><th>Balance</th><th>Ageing</th><th>Score</th><th>Reason</th><th>Action</th></tr></thead>
                <tbody>{visibleWorklist.map((row) => {
                  const decision = decisionsByStudent.get(row.studentId);
                  const decisionTone = decision?.chosenAction === "ESCALATE_FOR_REVIEW" ? "warning" : decision?.chosenAction === "DRAFT_REMINDER" ? "success" : "neutral";
                  return <tr key={row.studentId}>
                  <td><span className="rank">{row.rank}</span></td>
                  <td><strong>{row.studentName}</strong><span className="cellSub">{row.studentId}</span></td>
                  <td>{row.class}</td>
                  <td><strong>{row.outstanding}</strong><span className="cellSub">{row.daysOverdue ? `${row.daysOverdue} days overdue` : "Not overdue"}</span></td>
                  <td><StatusBadge tone={row.ageingBucket === "60+" ? "danger" : row.ageingBucket === "NOT_OVERDUE" ? "neutral" : "warning"}>{row.ageingBucket}</StatusBadge></td>
                  <td><strong>{row.score}</strong><span className="cellSub">{row.planCompliance}</span></td>
                  <td className="reasonCell">{row.reason}</td>
                  <td>{decision ? <><StatusBadge tone={decisionTone}>{decision.chosenAction.replaceAll("_", " ")}</StatusBadge><span className="cellSub">{decision.reason}</span></> : row.shouldContact ? <StatusBadge tone="danger">Contact now</StatusBadge> : <StatusBadge tone="neutral">Plan on file</StatusBadge>}</td>
                </tr>;
                })}</tbody>
              </table>
            </div>
          </section>
        )}

        {tab === "reminders" && (
          <section className="panel">
            <SectionHeader eyebrow="Human review required" title="Reminder drafts" detail="Messages are deterministic templates for accounts-office review. Nothing is sent." action={<StatusBadge tone="neutral"><FileText size={13} /> Draft only</StatusBadge>} />
            <div className="reviewBanner neutralBanner"><ShieldCheck size={17} /><span>Amounts come from the verified ledger and are checked before a draft is displayed.</span></div>
            <div className="draftGrid">
              {activeData.reminderDrafts.map((draft) => <article className="draftCard" key={draft.studentId}>
                <div className="draftTop"><div><strong>{draft.studentName}</strong><span>{draft.guardianName}</span></div><StatusBadge tone={draft.ageingBucket === "31-60" ? "warning" : "neutral"}>{draft.ageingBucket}</StatusBadge></div>
                <div className="draftMeta"><span>{draft.tone} / due {draft.dueDate}</span><strong>{draft.amount}</strong></div>
                <p className="draftMessage">{draft.message}</p>
                <div className="draftFooter"><StatusBadge tone="success"><CheckCircle2 size={12} /> {draft.validationNote}</StatusBadge><span>{draft.generationSource} / not sent</span>{liveRunId && user && <button type="button" className="smallAction" onClick={() => submitReviewAction("REMINDER", draft.studentId, "APPROVE_DRAFT")}>Approve draft</button>}</div>
              </article>)}
            </div>
            {activeData.reminderDrafts.length === 0 && <EmptyState icon={MessageSquareText} title="No drafts" detail="No eligible overdue family needs a reminder draft." />}
          </section>
        )}

        {tab === "insights" && (
          <>
            <div className="insightGrid">
              <section className="panel">
                <SectionHeader
                  eyebrow="Planning estimate"
                  title="30-day cash forecast"
                  detail="Derived from payment history and current eligible balances; it never changes the ledger."
                  action={<StatusBadge tone={forecast.summary.forecastConfidence === "LOW" ? "warning" : "success"}><TrendingUp size={13} /> {forecast.summary.forecastConfidence || "UNAVAILABLE"} confidence</StatusBadge>}
                />
                <dl className="metricList">
                  <div><dt>Expected cash inflow</dt><dd>{money(forecast.summary.expectedCashInflow)}</dd></div>
                  <div><dt>Expected outstanding</dt><dd>{money(forecast.summary.expectedOutstanding)}</dd></div>
                  <div><dt>Projected collection rate</dt><dd>{forecast.summary.projectedCollectionRatePercent ?? 0}%</dd></div>
                </dl>
                <p className="insightNote">{forecast.summary.limitation}</p>
              </section>

              <section className="panel">
                <SectionHeader
                  eyebrow="Financial controls"
                  title="Fee leakage scan"
                  detail="Exception signals from payments, refunds, transfers, adjustments, plans, and concessions."
                  action={<StatusBadge tone={highLeakageFindings.length ? "danger" : "success"}><ShieldAlert size={13} /> {highLeakageFindings.length} high severity</StatusBadge>}
                />
                <dl className="metricList">
                  <div><dt>Findings requiring review</dt><dd>{leakage.summary.findingCount || 0}</dd></div>
                  <div><dt>Potential amount at risk</dt><dd>{money(leakage.summary.amountAtRisk)}</dd></div>
                  <div><dt>Control status</dt><dd className={highLeakageFindings.length ? "dangerText" : "positiveText"}>{(leakage.summary.status || "UNAVAILABLE").replaceAll("_", " ")}</dd></div>
                </dl>
                <p className="insightNote">{leakage.summary.limitation}</p>
              </section>
            </div>

            <section className="panel">
              <SectionHeader eyebrow="By family" title="Likely collection timing" detail="The forecast is a review aid, with sparse fixture history explicitly labelled low confidence." />
              <div className="tableWrap">
                <table>
                  <thead><tr><th>Family</th><th>Forecastable balance</th><th>Recovery rate</th><th>Expected in 30 days</th><th>Delay risk</th><th>Evidence</th></tr></thead>
                  <tbody>{(forecast.studentForecasts || []).map((row) => <tr key={row.studentId}>
                    <td><strong>{row.studentName}</strong><span className="cellSub">{row.studentId} / {row.class}</span></td>
                    <td>{row.forecastableOutstanding}</td>
                    <td>{row.recoveryRatePercent}%<span className="cellSub">{row.historicalRecordCount} history record(s)</span></td>
                    <td className="positiveText"><strong>{row.expectedCollection}</strong></td>
                    <td><StatusBadge tone={row.delayRisk === "HIGH" ? "danger" : row.delayRisk === "MEDIUM" ? "warning" : "success"}>{row.delayRisk}</StatusBadge></td>
                    <td className="reasonCell">{row.reason}</td>
                  </tr>)}</tbody>
                </table>
              </div>
            </section>

            <section className="panel">
              <SectionHeader eyebrow="Human review queue" title="Leakage and integrity findings" detail="A finding is not a loss confirmation. It requires evidence-based review before any financial record changes." action={<StatusBadge tone="warning"><AlertTriangle size={13} /> {leakage.summary.findingCount || 0} findings</StatusBadge>} />
              <div className="tableWrap">
                <table>
                  <thead><tr><th>Finding</th><th>Student</th><th>Exposure</th><th>Severity</th><th>Evidence</th><th>Recommended action</th><th>Review</th></tr></thead>
                  <tbody>{(leakage.findings || []).map((finding) => <tr key={finding.findingId} className={finding.severity === "HIGH" ? "reviewRow" : ""}>
                    <td><strong>{finding.category.replaceAll("_", " ")}</strong><span className="cellSub">{finding.findingId}</span></td>
                    <td>{finding.studentId || <span className="mutedText">Unassigned</span>}</td>
                    <td>{finding.affectedAmount}</td>
                    <td><StatusBadge tone={finding.severity === "HIGH" ? "danger" : "warning"}>{finding.severity}</StatusBadge></td>
                    <td className="reasonCell">{finding.reason}<span className="cellSub">{finding.sourceReferences.join(", ")}</span></td>
                    <td className="reasonCell">{finding.recommendation}</td>
                    <td>{liveRunId && user ? <button type="button" className="smallAction" onClick={() => submitReviewAction("LEAKAGE", finding.findingId, "ACKNOWLEDGE_EXCEPTION")}>Record review</button> : <StatusBadge tone="warning">Review required</StatusBadge>}</td>
                  </tr>)}</tbody>
                </table>
              </div>
            </section>
          </>
        )}

        {tab === "audit" && (
          <section className="panel">
            <SectionHeader eyebrow="Traceability" title="Audit trail" detail="Every run, reconciliation decision, student position, and draft is timestamped." action={<StatusBadge tone="success"><ShieldCheck size={13} /> {activeData.auditEvents.length} events</StatusBadge>} />
            <div className="auditList">
              {activeData.auditEvents.map((event, index) => <article className="auditRow" key={`${event.eventType}-${index}`}>
                <span className={`auditDot ${event.eventType.includes("REVIEW") ? "auditWarn" : event.eventType.includes("COMPLETED") ? "auditSuccess" : ""}`} />
                <div className="auditMain"><strong>{event.eventType.replaceAll("_", " ")}</strong><span>{event.actor}</span></div>
                <time>{new Date(event.timestamp).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" })}</time>
              </article>)}
            </div>
          </section>
        )}

        <footer className="pageFooter"><span><ShieldCheck size={14} /> Figures are deterministic and traceable to source records.</span><span>{liveRunId ? "Live Firestore subscriptions active" : "Local JSON demo / Firestore workflow optional"}</span></footer>
      </main>
    </div>
  );
}

export default App;

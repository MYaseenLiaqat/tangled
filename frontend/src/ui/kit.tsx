import { CSSProperties, FormEvent, ReactNode, useEffect, useRef, useState } from "react";
import { Icon, IconName } from "./Icon";

/* Presentational building blocks shared by the pages. No data fetching here. */

export function Skeleton({ w = "100%", h = 16, r, style }: { w?: number | string; h?: number | string; r?: number; style?: CSSProperties }) {
  return <span className="skel" aria-hidden="true" style={{ width: w, height: h, borderRadius: r, ...style }} />;
}

/** Placeholder with the same footprint as the Overview (stat strip + two topic cards). */
export function OverviewSkeleton() {
  return <div className="skel-stack" role="status" aria-label="Loading topics…">
    <Skeleton h={92} r={14} />
    <Skeleton w={220} h={22} style={{ marginTop: 20 }} />
    <div className="topic-grid"><Skeleton h={196} r={14} /><Skeleton h={196} r={14} /></div>
  </div>;
}

export function ListSkeleton({ rows = 3, label = "Loading…", height = 60 }: { rows?: number; label?: string; height?: number }) {
  return <div className="skel-stack" role="status" aria-label={label}>{Array.from({ length: rows }, (_, i) => <Skeleton key={i} h={height} r={12} />)}</div>;
}

export function Empty({ icon = "spark", title, children, action }: { icon?: IconName | string; title: string; children?: ReactNode; action?: ReactNode }) {
  return <div className="empty"><span className="empty-icon"><Icon name={icon} /></span><span className="empty-title">{title}</span>{children && <small>{children}</small>}{action}</div>;
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="state" role="alert"><span className="empty-icon" style={{ background: "var(--bad-soft)", color: "var(--bad)" }}><Icon name="alert" /></span><p>{message}</p>{retry && <button className="btn" onClick={retry}><Icon name="refresh" />Try again</button>}</div>;
}

const STATUS: Record<string, { label: string; tone: string; icon?: IconName }> = {
  review: { label: "Needs attention", tone: "warn" },
  needs_attention: { label: "Needs attention", tone: "warn" },
  addressed: { label: "Addressed", tone: "ok", icon: "check" },
  false_alarm: { label: "Dismissed", tone: "neutral" },
  watch: { label: "Monitoring", tone: "info" },
  none: { label: "Not enough data", tone: "neutral" },
};

export function StatusPill({ status }: { status?: string | null }) {
  const s = STATUS[status || "review"] || STATUS.review;
  return <span className={`pill${s.tone === "neutral" ? "" : ` pill-${s.tone}`}`}>{s.icon ? <Icon name={s.icon} /> : <span className="dot" />}{s.label}</span>;
}

export function ConfidenceMeter({ level }: { level: string | null | undefined }) {
  const on = level === "High" ? 3 : level === "Medium" ? 2 : level ? 1 : 0;
  return <span className="meter" title="Confidence that this topic needs attention"><span className="meter-bars" aria-hidden="true">{[1, 2, 3].map(n => <i key={n} className={n <= on ? "on" : ""} />)}</span>{level ? `${level} confidence` : "Confidence pending"}</span>;
}

export function Bar({ value, tone, label }: { value: number; tone?: "ok" | "warn" | "bad"; label?: string }) {
  const pct = Math.max(0, Math.min(100, value * 100));
  return <div className={`bar${tone ? ` bar-${tone}` : ""}`} role="img" aria-label={label || `${Math.round(pct)} percent`}><i style={{ width: `${pct}%` }} /></div>;
}

/** Toast for transient confirmations. Announces politely and hides itself after 3 s. */
export function Toast({ message, onDone }: { message: string; onDone: () => void }) {
  useEffect(() => {
    if (!message) return;
    const timer = window.setTimeout(onDone, 3000);
    return () => window.clearTimeout(timer);
  }, [message]);
  return <div className="toast-region" aria-live="polite">{message && <div className="toast" role="status"><Icon name="check" />{message}</div>}</div>;
}

/** Modal confirm. With `requireText`, the confirm button unlocks only once that text is typed; it is passed to onConfirm. */
export function ConfirmDialog({ open, title, body, confirmLabel, danger, requireText, onConfirm, onCancel }: {
  open: boolean; title: string; body: ReactNode; confirmLabel: string; danger?: boolean; requireText?: string;
  onConfirm: (typed: string) => void; onCancel: () => void;
}) {
  const [typed, setTyped] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!open) return;
    setTyped("");
    (requireText ? input.current : cancel.current)?.focus();
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onCancel(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);
  if (!open) return null;
  const ready = !requireText || typed === requireText;
  function submit(event: FormEvent) { event.preventDefault(); if (ready) onConfirm(typed); }
  return <div className="dialog-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onCancel(); }}>
    <form className="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title" onSubmit={submit}>
      <h2 id="dialog-title">{title}</h2>
      <div>{body}</div>
      {requireText && <label className="field">Type <b>{requireText}</b> to confirm<input ref={input} value={typed} onChange={event => setTyped(event.target.value)} autoComplete="off" /></label>}
      <div className="dialog-actions"><button ref={cancel} type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button><button className={`btn ${danger ? "btn-danger-solid" : "btn-primary"}`} disabled={!ready}>{confirmLabel}</button></div>
    </form>
  </div>;
}

/** Copies text and shows a short "Copied" state on the button. */
export function CopyButton({ text, label, className = "btn" }: { text: string; label: string; className?: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try { await navigator.clipboard.writeText(text); setCopied(true); window.setTimeout(() => setCopied(false), 1600); }
    catch { window.prompt("Copy this:", text); }
  }
  return <button type="button" className={className} onClick={copy} aria-live="polite"><Icon name={copied ? "check" : "copy"} />{copied ? "Copied" : label}</button>;
}

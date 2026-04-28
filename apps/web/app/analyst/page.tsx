"use client";

import { useEffect, useState } from "react";
import { ClipboardCheck, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { BorrowerProfile, Review } from "@/types/api";
import { ResponsibleAIPanel } from "@/components/ResponsibleAIPanel";
import { ScoreCard } from "@/components/ScoreCard";
import { Empty, ErrorMessage, Loading } from "@/components/State";
import { Shell } from "@/components/Shell";

type AuditLog = { id: number; actor_email?: string; action: string; metadata: Record<string, unknown>; created_at: string };

export default function AnalystPage() {
  const [cases, setCases] = useState<BorrowerProfile[]>([]);
  const [selected, setSelected] = useState<BorrowerProfile | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [decision, setDecision] = useState("PENDING");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function loadCases() {
    try {
      const data = await apiFetch<BorrowerProfile[]>("/analyst/cases/");
      setCases(data);
      if (!selected && data[0]) await openCase(data[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat kasus analis.");
    } finally {
      setLoading(false);
    }
  }

  async function openCase(id: number) {
    const detail = await apiFetch<BorrowerProfile>(`/analyst/cases/${id}/`);
    setSelected(detail);
    setDecision(detail.reviews?.[0]?.final_human_decision ?? "PENDING");
    setLogs(await apiFetch<AuditLog[]>(`/borrower-profiles/${id}/audit-logs/`));
  }

  useEffect(() => {
    loadCases();
  }, []);

  async function deepscore() {
    if (!selected) return;
    setBusy(true);
    try {
      await apiFetch<Review>(`/analyst/cases/${selected.id}/deepscore/`, { method: "POST", body: JSON.stringify({}) });
      await openCase(selected.id);
      await loadCases();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menjalankan DeepScore.");
    } finally {
      setBusy(false);
    }
  }

  async function saveDecision() {
    const review = selected?.reviews?.[0];
    if (!review) return;
    setBusy(true);
    try {
      await apiFetch(`/analyst/reviews/${review.id}/decision/`, { method: "PATCH", body: JSON.stringify({ final_human_decision: decision, analyst_notes: notes }) });
      await openCase(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan keputusan manusia.");
    } finally {
      setBusy(false);
    }
  }

  const review = selected?.reviews?.[0] ?? selected?.latest_review;
  const check = selected?.instant_checks?.[0] ?? selected?.latest_instant_check;

  return (
    <Shell title="Dashboard Analis Kredit">
      {loading && <Loading />}
      {error && <ErrorMessage error={error} />}
      {!loading && cases.length === 0 && <Empty text="Belum ada kasus yang dikirim ke analis." />}
      <div className="mt-5 grid gap-4 lg:grid-cols-[300px_1fr]">
        <aside className="rounded-md border border-black/10 bg-white p-4">
          <h2 className="font-semibold">Kasus submitted</h2>
          <div className="mt-3 space-y-2">
            {cases.map((item) => (
              <button key={item.id} onClick={() => openCase(item.id)} className={`focus-ring w-full rounded-md border px-3 py-2 text-left text-sm ${selected?.id === item.id ? "border-mint bg-mint/5" : "border-black/10"}`}>
                <span className="block font-medium">{item.business_name}</span>
                <span className="text-black/60">{item.status}</span>
              </button>
            ))}
          </div>
        </aside>
        {selected && (
          <section className="space-y-4">
            <div className="rounded-md border border-black/10 bg-white p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold">{selected.business_name}</h2>
                  <p className="mt-1 text-sm text-black/60">{selected.financing_purpose}</p>
                </div>
                <button disabled={busy} onClick={deepscore} className="focus-ring inline-flex items-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                  <RefreshCw size={16} /> DeepScore
                </button>
              </div>
            </div>
            {review && <ScoreCard review={review} />}
            <div className="grid gap-4 xl:grid-cols-2">
              <Panel title="Bukti dan ekstraksi">
                {(selected.evidence_items ?? []).map((item) => (
                  <div key={item.id} className="mb-3 rounded-md border border-black/10 p-3 text-sm">
                    <p className="font-medium">{item.original_filename}</p>
                    <p className="text-black/60">{item.evidence_type} | {item.source_type} | {item.ai_status}</p>
                    <p className="mt-2 text-black/70">{item.extraction_result?.extracted_text ?? "Belum diproses."}</p>
                  </div>
                ))}
              </Panel>
              <Panel title="Instant Evidence Check">
                {check ? (
                  <div className="text-sm">
                    <p>Kelengkapan {check.data_completeness_score}% | Kualitas {check.evidence_quality_score}%</p>
                    <p className="mt-2 text-black/65">{check.ocr_summary}</p>
                    <ul className="mt-2 list-disc pl-5">{check.recommended_next_steps.map((step) => <li key={step}>{step}</li>)}</ul>
                  </div>
                ) : <p className="text-sm text-black/60">Belum ada hasil check.</p>}
              </Panel>
              <Panel title="Sinyal positif">
                <List items={review?.positive_signals ?? []} empty="Belum ada DeepScore." />
              </Panel>
              <Panel title="Red flags">
                <List items={review?.red_flags ?? []} empty="Tidak ada red flag utama atau DeepScore belum dijalankan." />
              </Panel>
              <Panel title="Keputusan manusia">
                <select className="focus-ring w-full rounded-md border border-black/15 px-3 py-2 text-sm" value={decision} onChange={(event) => setDecision(event.target.value)}>
                  {["PENDING", "NEEDS_MORE_DATA", "RECOMMENDED_FOR_REVIEW", "NOT_RECOMMENDED_AT_THIS_STAGE"].map((item) => <option key={item}>{item}</option>)}
                </select>
                <textarea className="focus-ring mt-2 min-h-24 w-full rounded-md border border-black/15 px-3 py-2 text-sm" placeholder="Catatan analis" value={notes} onChange={(event) => setNotes(event.target.value)} />
                <button disabled={!review || busy} onClick={saveDecision} className="focus-ring mt-2 inline-flex items-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                  <ClipboardCheck size={16} /> Simpan
                </button>
              </Panel>
              <Panel title="Audit trail">
                <div className="space-y-2 text-sm">
                  {logs.map((log) => <p key={log.id} className="rounded-md bg-paper p-2">{log.action} oleh {log.actor_email ?? "system"}</p>)}
                </div>
              </Panel>
            </div>
            <ResponsibleAIPanel consentGiven={selected.consent?.consent_given} />
          </section>
        )}
      </div>
    </Shell>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-md border border-black/10 bg-white p-4"><h3 className="mb-3 font-semibold">{title}</h3>{children}</section>;
}

function List({ items, empty }: { items: string[]; empty: string }) {
  if (!items.length) return <p className="text-sm text-black/60">{empty}</p>;
  return <ul className="list-disc pl-5 text-sm text-black/70">{items.map((item) => <li key={item}>{item}</li>)}</ul>;
}

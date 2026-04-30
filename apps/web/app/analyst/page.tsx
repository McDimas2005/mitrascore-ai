"use client";

import { useEffect, useState } from "react";
import { ClipboardCheck, Handshake, RefreshCw, RotateCcw, Trash2 } from "lucide-react";
import { apiFetch, getUser } from "@/lib/api";
import type { BorrowerProfile, Review, User } from "@/types/api";
import { ActionAvailability } from "@/components/ActionAvailability";
import { EvidenceSourceBadge } from "@/components/EvidenceSourceBadge";
import { ResponsibleAIPanel } from "@/components/ResponsibleAIPanel";
import { ScoreCard } from "@/components/ScoreCard";
import { Empty, ErrorMessage, Loading } from "@/components/State";
import { Shell } from "@/components/Shell";
import { VerificationReadinessPanel } from "@/components/VerificationReadinessPanel";
import { WorkflowPanel } from "@/components/WorkflowPanel";

type AuditLog = { id: number; actor_email?: string; action: string; metadata: Record<string, unknown>; created_at: string };

const decisionOptions = [
  { value: "PENDING", label: "Pending - masih direview" },
  { value: "NEEDS_MORE_DATA", label: "Perlu data tambahan" },
  { value: "RECOMMENDED_FOR_REVIEW", label: "Rekomendasikan review pembiayaan lanjutan" },
  { value: "APPROVED_FOR_FINANCING", label: "Setujui untuk proses pembiayaan" },
  { value: "NOT_RECOMMENDED_AT_THIS_STAGE", label: "Belum direkomendasikan saat ini" },
  { value: "DECLINED", label: "Tolak pada review manusia" }
];

export default function AnalystPage() {
  const [cases, setCases] = useState<BorrowerProfile[]>([]);
  const [selected, setSelected] = useState<BorrowerProfile | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [decision, setDecision] = useState("PENDING");
  const [notes, setNotes] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [savingDecision, setSavingDecision] = useState(false);
  const [requestingVerification, setRequestingVerification] = useState(false);
  const [error, setError] = useState("");
  const [decisionStatus, setDecisionStatus] = useState("");

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
    const latestReview = detail.reviews?.[0] ?? detail.latest_review;
    setSelected(detail);
    setDecision(latestReview?.final_human_decision ?? "PENDING");
    setNotes(latestReview?.analyst_notes ?? "");
    setDecisionStatus("");
    setLogs(await apiFetch<AuditLog[]>(`/borrower-profiles/${id}/audit-logs/`));
  }

  useEffect(() => {
    setUser(getUser());
    loadCases();
  }, []);

  async function deepscore() {
    if (!selected) return;
    setBusy(true);
    setError("");
    setDecisionStatus("");
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
    const currentCase = selected;
    if (!currentCase) return;
    const review = currentCase?.reviews?.[0] ?? currentCase?.latest_review;
    if (!review) {
      setError("Jalankan DeepScore dulu sebelum menyimpan keputusan manusia.");
      return;
    }
    setSavingDecision(true);
    setError("");
    setDecisionStatus("");
    try {
      await apiFetch(`/analyst/reviews/${review.id}/decision/`, { method: "PATCH", body: JSON.stringify({ final_human_decision: decision, analyst_notes: notes }) });
      await openCase(currentCase.id);
      setDecisionStatus("Keputusan manusia tersimpan.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan keputusan manusia.");
    } finally {
      setSavingDecision(false);
    }
  }

  async function resetDecision() {
    setDecision("PENDING");
    const currentCase = selected;
    if (!currentCase) return;
    const review = currentCase?.reviews?.[0] ?? currentCase?.latest_review;
    if (!review) {
      setError("Jalankan DeepScore dulu sebelum membatalkan keputusan manusia.");
      return;
    }
    setSavingDecision(true);
    setError("");
    setDecisionStatus("");
    try {
      await apiFetch(`/analyst/reviews/${review.id}/decision/`, { method: "PATCH", body: JSON.stringify({ final_human_decision: "PENDING", analyst_notes: "" }) });
      setNotes("");
      await openCase(currentCase.id);
      setDecisionStatus("Keputusan manusia dikembalikan ke PENDING.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal membatalkan keputusan manusia.");
    } finally {
      setSavingDecision(false);
    }
  }

  async function requestFieldVerification() {
    const currentCase = selected;
    if (!currentCase) return;
    const currentReview = currentCase?.reviews?.[0] ?? currentCase?.latest_review;
    if (!currentReview) {
      setError("Jalankan DeepScore dulu sebelum meminta verifikasi field agent.");
      return;
    }
    setRequestingVerification(true);
    setError("");
    setDecisionStatus("");
    try {
      const detail = await apiFetch<BorrowerProfile>(`/analyst/cases/${currentCase.id}/request-field-verification/`, {
        method: "POST",
        body: JSON.stringify({ analyst_notes: notes })
      });
      setSelected(detail);
      setDecision("NEEDS_MORE_DATA");
      setNotes(detail.reviews?.[0]?.analyst_notes ?? detail.latest_review?.analyst_notes ?? "");
      setDecisionStatus("Permintaan verifikasi field agent terkirim.");
      setLogs(await apiFetch<AuditLog[]>(`/borrower-profiles/${currentCase.id}/audit-logs/`));
      await loadCases();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal meminta verifikasi field agent.");
    } finally {
      setRequestingVerification(false);
    }
  }

  async function deleteSelectedCase() {
    if (!selected || !window.confirm("Hapus kasus ini dari demo lokal?")) return;
    setBusy(true);
    setError("");
    setDecisionStatus("");
    try {
      await apiFetch(`/borrower-profiles/${selected.id}/`, { method: "DELETE" });
      setSelected(null);
      setLogs([]);
      await loadCases();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menghapus kasus.");
    } finally {
      setBusy(false);
    }
  }

  const review = selected?.reviews?.[0] ?? selected?.latest_review;
  const check = selected?.instant_checks?.[0] ?? selected?.latest_instant_check;
  const approvalBlocked = decision === "APPROVED_FOR_FINANCING" && selected?.verification_readiness && !selected.verification_readiness.approval_ready;
  const savedDecision = review?.final_human_decision;
  const isClosedReview = ["DECLINED", "APPROVED_FOR_FINANCING"].includes(savedDecision ?? "");
  const declinedNeedsNotes = decision === "DECLINED" && !notes.trim();
  const deepscoreReason = !selected ? "Pilih kasus analis terlebih dahulu." :
    (isClosedReview ? "Kasus sudah memiliki keputusan final. Buka ulang ke Pending hanya jika ada koreksi resmi." : "");
  const saveDecisionReason = !review ? "Jalankan DeepScore terlebih dahulu sebelum menyimpan keputusan manusia." :
    (approvalBlocked ? "Approval belum bisa disimpan karena bukti kunci belum diverifikasi agen." : "") ||
    (declinedNeedsNotes ? "Alasan penolakan wajib diisi sebelum menyimpan keputusan final." : "");
  const resetDecisionReason = !review ? "Jalankan DeepScore terlebih dahulu sebelum membatalkan keputusan manusia." : "";
  const verificationRequestReason = !review ? "Jalankan DeepScore terlebih dahulu sebelum meminta verifikasi field agent." :
    (isClosedReview ? "Kasus sudah final. Buka ulang ke Pending hanya jika ada koreksi resmi." : "") ||
    (!selected?.verification_readiness || selected.verification_readiness.approval_ready ? "Verifikasi kunci sudah terpenuhi, tidak perlu request verifikasi tambahan." : "");

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
                <span className="text-black/60">{item.status_label ?? item.status}</span>
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
                  <p className="mt-1 text-sm font-medium text-mint">{selected.status_label ?? selected.status}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button disabled={busy || isClosedReview} title={deepscoreReason || undefined} onClick={deepscore} className="focus-ring inline-flex items-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                    <RefreshCw size={16} /> DeepScore
                  </button>
                  {user?.role === "ADMIN" && (
                    <button disabled={busy} onClick={deleteSelectedCase} className="focus-ring inline-flex items-center gap-2 rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 disabled:opacity-50">
                      <Trash2 size={16} /> Hapus
                    </button>
                  )}
                </div>
              </div>
              <ActionAvailability reasons={[deepscoreReason]} />
            </div>
            <WorkflowPanel profile={selected} role={user?.role === "ADMIN" ? "ADMIN" : "ANALYST"} />
            {isClosedReview && (
              <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-900">
                <p className="font-semibold">Kasus berada pada keputusan final</p>
                <p className="mt-1">
                  DeepScore ulang dan perubahan owner/field agent diblokir. Gunakan undo ke pending hanya untuk koreksi keputusan atau pembukaan ulang resmi.
                </p>
              </div>
            )}
            <VerificationReadinessPanel profile={selected} />
            {review && <ScoreCard review={review} />}
            <div className="grid gap-4 xl:grid-cols-2">
              <Panel title="Bukti dan ekstraksi">
                {(selected.evidence_items ?? []).map((item) => (
                  <div key={item.id} className="mb-3 rounded-md border border-black/10 p-3 text-sm">
                    <p className="font-medium">{item.original_filename}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-black/60">
                      <span>{item.evidence_type}</span>
                      <EvidenceSourceBadge item={item} />
                      <span>{item.ai_status}</span>
                      <span>{item.storage_backend === "AZURE_BLOB" ? "Azure Blob private" : "Local file"}</span>
                    </div>
                    {item.field_agent_note && <p className="mt-2 text-xs text-black/60">Catatan agen: {item.field_agent_note}</p>}
                    {item.extraction_result?.quality_flags?.length ? (
                      <p className="mt-2 text-xs text-saffron">{item.extraction_result.quality_flags.join("; ")}</p>
                    ) : null}
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
                <select className="focus-ring w-full rounded-md border border-black/15 px-3 py-2 text-sm" value={decision} onChange={(event) => { setDecision(event.target.value); setDecisionStatus(""); }}>
                  {decisionOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                </select>
                {review?.final_human_decision_label && (
                  <p className="mt-2 rounded-md bg-paper p-2 text-sm text-black/70">Keputusan tersimpan: {review.final_human_decision_label}</p>
                )}
                {approvalBlocked && (
                  <p className="mt-2 rounded-md border border-saffron/40 bg-saffron/10 p-2 text-sm text-black/75">
                    Approval belum siap. Minta field agent memverifikasi bukti kunci sesuai panel verifikasi.
                  </p>
                )}
                {decision === "DECLINED" && (
                  <p className="mt-2 rounded-md border border-red-200 bg-red-50 p-2 text-sm text-red-900">
                    Penolakan akan menutup siklus pengajuan ini. Owner dan field agent tidak bisa mengubah, menambah bukti, atau kirim ulang kecuali kasus dibuka ulang.
                  </p>
                )}
                <textarea className="focus-ring mt-2 min-h-24 w-full rounded-md border border-black/15 px-3 py-2 text-sm" placeholder="Catatan analis, permintaan data, atau alasan keputusan" value={notes} onChange={(event) => { setNotes(event.target.value); setDecisionStatus(""); }} />
                {declinedNeedsNotes && (
                  <p className="mt-2 text-sm font-medium text-red-700">Alasan penolakan wajib diisi sebelum menyimpan keputusan final.</p>
                )}
                <div className="mt-2 flex flex-wrap gap-2">
                  <button disabled={!review || busy || savingDecision || Boolean(approvalBlocked) || declinedNeedsNotes} title={saveDecisionReason || undefined} onClick={saveDecision} className="focus-ring inline-flex items-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                    <ClipboardCheck size={16} /> {savingDecision ? "Menyimpan..." : "Simpan"}
                  </button>
                  <button
                    disabled={!review || requestingVerification || isClosedReview || Boolean(selected?.verification_readiness?.approval_ready)}
                    title={verificationRequestReason || undefined}
                    onClick={requestFieldVerification}
                    className="focus-ring inline-flex items-center gap-2 rounded-md bg-saffron px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
                  >
                    <Handshake size={16} /> {requestingVerification ? "Mengirim..." : "Minta verifikasi agen"}
                  </button>
                  <button disabled={!review || busy || savingDecision} title={resetDecisionReason || undefined} onClick={resetDecision} className="focus-ring inline-flex items-center gap-2 rounded-md border border-black/15 px-3 py-2 text-sm font-medium disabled:opacity-50">
                    <RotateCcw size={16} /> {isClosedReview ? "Buka ulang ke Pending" : "Undo ke Pending"}
                  </button>
                </div>
                <ActionAvailability reasons={[saveDecisionReason, verificationRequestReason, resetDecisionReason]} />
                {decisionStatus && <p className="mt-2 text-sm font-medium text-mint">{decisionStatus}</p>}
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

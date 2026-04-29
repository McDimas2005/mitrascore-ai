"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, FileText, RefreshCw, Save, Send, Trash2, Upload, Wand2 } from "lucide-react";
import { apiFetch, emptyProfile } from "@/lib/api";
import type { BorrowerProfile, EvidenceItem } from "@/types/api";
import { EvidenceSourceBadge, EvidenceSourceDetails } from "@/components/EvidenceSourceBadge";
import { ErrorMessage, Loading } from "@/components/State";
import { Shell } from "@/components/Shell";
import { WorkflowPanel } from "@/components/WorkflowPanel";

export default function FieldAgentPage() {
  const [profiles, setProfiles] = useState<BorrowerProfile[]>([]);
  const [selected, setSelected] = useState<BorrowerProfile | null>(null);
  const [form, setForm] = useState<Partial<BorrowerProfile>>({ ...emptyProfile, business_name: "Warung dampingan baru" });
  const [file, setFile] = useState<File | null>(null);
  const [note, setNote] = useState("");
  const [sourceType, setSourceType] = useState("AGENT_ASSISTED");
  const [evidenceType, setEvidenceType] = useState("RECEIPT");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const data = await apiFetch<BorrowerProfile[]>("/borrower-profiles/");
      setProfiles(data);
      const next = selected ? data.find((item) => item.id === selected.id) ?? data[0] ?? null : data[0] ?? null;
      if (next) await openCase(next.id);
      else setSelected(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat kasus agen.");
    } finally {
      setLoading(false);
    }
  }

  async function openCase(id: number) {
    const detail = await apiFetch<BorrowerProfile>(`/borrower-profiles/${id}/`);
    setSelected(detail);
  }

  useEffect(() => {
    load();
  }, []);

  async function createCase() {
    setBusy(true);
    try {
      const data = await apiFetch<BorrowerProfile>("/borrower-profiles/", { method: "POST", body: JSON.stringify(form) });
      setSelected(data);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal membuat profil dampingan.");
    } finally {
      setBusy(false);
    }
  }

  async function saveSelectedProfile() {
    if (!selected) return;
    setBusy(true);
    try {
      const data = await apiFetch<BorrowerProfile>(`/borrower-profiles/${selected.id}/`, {
        method: "PATCH",
        body: JSON.stringify({
          business_name: selected.business_name,
          business_category: selected.business_category,
          financing_purpose: selected.financing_purpose,
          business_note: selected.business_note
        })
      });
      setSelected(data);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan profil dampingan.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteSelectedProfile() {
    if (!selected || !window.confirm("Hapus kasus dampingan ini?")) return;
    setBusy(true);
    try {
      await apiFetch(`/borrower-profiles/${selected.id}/`, { method: "DELETE" });
      setSelected(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menghapus kasus dampingan.");
    } finally {
      setBusy(false);
    }
  }

  async function upload() {
    if (!selected || !file) return;
    setBusy(true);
    try {
      const body = new FormData();
      body.append("evidence_type", evidenceType);
      body.append("source_type", sourceType);
      body.append("field_agent_note", note);
      body.append("file", file);
      const item = await apiFetch<EvidenceItem>(`/borrower-profiles/${selected.id}/evidence/`, { method: "POST", body });
      await apiFetch(`/evidence/${item.id}/process/`, { method: "POST", body: JSON.stringify({}) });
      await load();
      setFile(null);
      setNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal unggah bukti agen. Pastikan consent sudah diberikan.");
    } finally {
      setBusy(false);
    }
  }

  async function updateEvidenceSource(item: EvidenceItem, nextSourceType: string) {
    let fieldAgentNote = item.field_agent_note;
    if (nextSourceType === "AGENT_VERIFIED" && !fieldAgentNote.trim()) {
      fieldAgentNote = window.prompt("Catatan verifikasi wajib: jelaskan apa yang dilihat/dicocokkan agen.", "")?.trim() ?? "";
      if (!fieldAgentNote) return;
    }
    setBusy(true);
    try {
      await apiFetch(`/evidence/${item.id}/source-type/`, {
        method: "PATCH",
        body: JSON.stringify({ source_type: nextSourceType, field_agent_note: fieldAgentNote })
      });
      if (selected) await openCase(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mengubah status bukti.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteEvidence(id: number) {
    if (!window.confirm("Hapus bukti ini?")) return;
    setBusy(true);
    try {
      await apiFetch(`/evidence/${id}/`, { method: "DELETE" });
      if (selected) await openCase(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menghapus bukti.");
    } finally {
      setBusy(false);
    }
  }

  async function runInstantCheck() {
    if (!selected) return;
    setBusy(true);
    try {
      await apiFetch(`/borrower-profiles/${selected.id}/instant-check/`, { method: "POST", body: JSON.stringify({}) });
      await openCase(selected.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menjalankan Instant Evidence Check.");
    } finally {
      setBusy(false);
    }
  }

  async function submitAnalyst() {
    if (!selected) return;
    setBusy(true);
    try {
      const data = await apiFetch<BorrowerProfile>(`/borrower-profiles/${selected.id}/submit-to-analyst/`, { method: "POST", body: JSON.stringify({}) });
      setSelected(data);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Belum bisa dikirim ke analis. Jalankan check yang cukup dulu.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Shell title="Dashboard Field Agent">
      {loading && <Loading />}
      {error && <ErrorMessage error={error} />}
      <div className="mt-5 grid gap-4 lg:grid-cols-[320px_1fr]">
        <aside className="rounded-md border border-black/10 bg-white p-4">
          <h2 className="font-semibold">Kasus dampingan</h2>
          <div className="mt-3 space-y-2">
            {profiles.map((profile) => (
              <button key={profile.id} onClick={() => openCase(profile.id)} className={`focus-ring w-full rounded-md border px-3 py-2 text-left text-sm ${selected?.id === profile.id ? "border-mint bg-mint/5" : "border-black/10"}`}>
                <span className="block font-medium">{profile.business_name}</span>
                <span className="text-black/60">{profile.status_label ?? profile.status}</span>
              </button>
            ))}
          </div>
          <div className="mt-5 border-t border-black/10 pt-4">
            <h3 className="text-sm font-semibold">Buat profil dampingan</h3>
            <input className="focus-ring mt-2 w-full rounded-md border border-black/15 px-3 py-2 text-sm" value={form.business_name ?? ""} onChange={(event) => setForm({ ...form, business_name: event.target.value })} />
            <button disabled={busy} onClick={createCase} className="focus-ring mt-2 inline-flex items-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
              <Wand2 size={16} /> Buat
            </button>
          </div>
        </aside>
        <section className="rounded-md border border-black/10 bg-white p-4">
          {selected ? (
            <>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-xl font-semibold">{selected.business_name}</h2>
                  <p className="mt-1 text-sm text-black/60">{selected.business_category || "Kategori belum diisi"} | {selected.status_label ?? selected.status}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button disabled={busy} onClick={runInstantCheck} className="focus-ring inline-flex items-center gap-2 rounded-md border border-black/15 px-3 py-2 text-sm font-medium disabled:opacity-50">
                    <RefreshCw size={16} /> Check
                  </button>
                  <button disabled={!selected.latest_instant_check?.can_submit_to_analyst || busy} onClick={submitAnalyst} className="focus-ring inline-flex items-center gap-2 rounded-md bg-saffron px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                    <Send size={16} /> Kirim ke Analis
                  </button>
                  <button disabled={busy} onClick={deleteSelectedProfile} className="focus-ring inline-flex items-center gap-2 rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 disabled:opacity-50">
                    <Trash2 size={16} /> Hapus
                  </button>
                </div>
              </div>
              <div className="mt-4">
                <WorkflowPanel profile={selected} role="FIELD_AGENT" />
              </div>
              <div className="mt-4 rounded-md border border-black/10 bg-paper p-3 text-sm">
                <p className="font-semibold">Makna status bukti</p>
                <div className="mt-2 grid gap-2 md:grid-cols-3">
                  <SourceDefinition
                    title="Self uploaded"
                    text="Owner mengunggah bukti sendiri. Bukti dipakai untuk kelengkapan dan OCR, tanpa klaim verifikasi lapangan."
                  />
                  <SourceDefinition
                    title="Agent assisted"
                    text="Agen membantu mengambil atau mengunggah bukti. Ini mencatat pendampingan, tetapi belum berarti agen memverifikasi keaslian atau konteks bukti."
                  />
                  <SourceDefinition
                    title="Agent verified"
                    text="Agen sudah mencocokkan bukti dengan observasi usaha atau dokumen asli. Status ini menambah +4 poin kualitas bukti per item sebelum batas skor dan wajib punya catatan verifikasi."
                  />
                </div>
              </div>
              {selected.latest_review && (
                <div className="mt-4 rounded-md border border-black/10 bg-paper p-3 text-sm">
                  <div className="flex items-center gap-2 font-semibold">
                    <CheckCircle2 size={17} className="text-mint" />
                    Hasil review analis: {selected.latest_review.final_human_decision_label}
                  </div>
                  {selected.latest_review.analyst_notes && (
                    <div className="mt-3 flex items-start gap-2 text-black/70">
                      <FileText size={16} className="mt-0.5 shrink-0 text-mint" />
                      <p>{selected.latest_review.analyst_notes}</p>
                    </div>
                  )}
                </div>
              )}
              {selected.business_note?.includes("Permintaan bantuan agen:") && (
                <div className="mt-4 rounded-md border border-mint/30 bg-mint/5 p-3 text-sm">
                  <p className="font-semibold text-mint">Info kunjungan dari UMKM</p>
                  <pre className="mt-2 whitespace-pre-wrap font-sans leading-6 text-black/70">{selected.business_note}</pre>
                </div>
              )}
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <input className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm" value={selected.business_name ?? ""} onChange={(event) => setSelected({ ...selected, business_name: event.target.value })} />
                <input className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm" placeholder="Kategori usaha" value={selected.business_category ?? ""} onChange={(event) => setSelected({ ...selected, business_category: event.target.value })} />
                <textarea className="focus-ring min-h-20 rounded-md border border-black/15 px-3 py-2 text-sm sm:col-span-2" placeholder="Tujuan pembiayaan" value={selected.financing_purpose ?? ""} onChange={(event) => setSelected({ ...selected, financing_purpose: event.target.value })} />
                <textarea className="focus-ring min-h-20 rounded-md border border-black/15 px-3 py-2 text-sm sm:col-span-2" placeholder="Catatan usaha / observasi" value={selected.business_note ?? ""} onChange={(event) => setSelected({ ...selected, business_note: event.target.value })} />
              </div>
              <button disabled={busy} onClick={saveSelectedProfile} className="focus-ring mt-3 inline-flex items-center gap-2 rounded-md bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                <Save size={16} /> Simpan Perubahan
              </button>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <select className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm" value={evidenceType} onChange={(event) => setEvidenceType(event.target.value)}>
                  {["BUSINESS_PHOTO", "RECEIPT", "INVOICE", "SUPPLIER_NOTE", "SALES_NOTE", "QRIS_SCREENSHOT", "OTHER"].map((type) => <option key={type}>{type}</option>)}
                </select>
                <select className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm" value={sourceType} onChange={(event) => setSourceType(event.target.value)}>
                  <option value="AGENT_ASSISTED">Agent assisted - dibantu agen</option>
                  <option value="AGENT_VERIFIED">Agent verified - diverifikasi agen</option>
                  <option value="SELF_UPLOADED">Self uploaded - unggahan owner</option>
                </select>
                <input className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm sm:col-span-2" type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
                <textarea className="focus-ring min-h-24 rounded-md border border-black/15 px-3 py-2 text-sm sm:col-span-2" placeholder="Catatan observasi agen" value={note} onChange={(event) => setNote(event.target.value)} />
              </div>
              <button disabled={!file || busy || (sourceType === "AGENT_VERIFIED" && !note.trim())} onClick={upload} className="focus-ring mt-3 inline-flex items-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                <Upload size={16} /> Unggah dan proses
              </button>
              {sourceType === "AGENT_VERIFIED" && !note.trim() && (
                <p className="mt-2 text-sm text-saffron">Catatan verifikasi wajib untuk bukti agent verified.</p>
              )}
              <div className="mt-5 space-y-2">
                {(selected.evidence_items ?? []).map((item) => (
                  <div key={item.id} className="rounded-md border border-black/10 p-3 text-sm">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="font-medium">{item.original_filename}</p>
                        <div className="mt-1 flex flex-wrap items-center gap-2 text-black/60">
                          <span>{item.evidence_type}</span>
                          <EvidenceSourceBadge item={item} />
                          <span>{item.ai_status}</span>
                        </div>
                        <EvidenceSourceDetails item={item} />
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button disabled={busy || item.source_type === "AGENT_ASSISTED"} onClick={() => updateEvidenceSource(item, "AGENT_ASSISTED")} title="Mark as agent assisted: agent helped collect/upload, but has not verified source context." className="focus-ring rounded-md border border-black/15 px-3 py-2 disabled:opacity-50">Mark assisted</button>
                        <button disabled={busy || item.source_type === "AGENT_VERIFIED"} onClick={() => updateEvidenceSource(item, "AGENT_VERIFIED")} title="Mark as agent verified: requires verification note and increases evidence quality." className="focus-ring rounded-md border border-mint px-3 py-2 text-mint disabled:opacity-50">Mark verified</button>
                        <button disabled={busy} onClick={() => deleteEvidence(item.id)} className="focus-ring inline-flex items-center gap-2 rounded-md border border-red-200 px-3 py-2 text-red-700 disabled:opacity-50">
                          <Trash2 size={15} /> Hapus
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-black/60">Belum ada kasus dampingan.</p>
          )}
        </section>
      </div>
    </Shell>
  );
}

function SourceDefinition({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-md border border-black/10 bg-white p-3">
      <p className="font-medium">{title}</p>
      <p className="mt-1 text-black/65">{text}</p>
    </div>
  );
}

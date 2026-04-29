"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Save, Trash2, Upload, Wand2 } from "lucide-react";
import { apiFetch, emptyProfile } from "@/lib/api";
import type { BorrowerProfile, EvidenceItem } from "@/types/api";
import { ErrorMessage, Loading } from "@/components/State";
import { Shell } from "@/components/Shell";

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
    setBusy(true);
    try {
      await apiFetch(`/evidence/${item.id}/source-type/`, {
        method: "PATCH",
        body: JSON.stringify({ source_type: nextSourceType, field_agent_note: item.field_agent_note })
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
                <span className="text-black/60">{profile.status}</span>
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
                  <p className="mt-1 text-sm text-black/60">{selected.business_category || "Kategori belum diisi"} | {selected.status}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button disabled={busy} onClick={runInstantCheck} className="focus-ring inline-flex items-center gap-2 rounded-md border border-black/15 px-3 py-2 text-sm font-medium disabled:opacity-50">
                    <RefreshCw size={16} /> Check
                  </button>
                  <button disabled={busy} onClick={deleteSelectedProfile} className="focus-ring inline-flex items-center gap-2 rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 disabled:opacity-50">
                    <Trash2 size={16} /> Hapus
                  </button>
                </div>
              </div>
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
                  {["AGENT_ASSISTED", "AGENT_VERIFIED", "SELF_UPLOADED"].map((type) => <option key={type}>{type}</option>)}
                </select>
                <input className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm sm:col-span-2" type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
                <textarea className="focus-ring min-h-24 rounded-md border border-black/15 px-3 py-2 text-sm sm:col-span-2" placeholder="Catatan observasi agen" value={note} onChange={(event) => setNote(event.target.value)} />
              </div>
              <button disabled={!file || busy} onClick={upload} className="focus-ring mt-3 inline-flex items-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                <Upload size={16} /> Unggah dan proses
              </button>
              <div className="mt-5 space-y-2">
                {(selected.evidence_items ?? []).map((item) => (
                  <div key={item.id} className="rounded-md border border-black/10 p-3 text-sm">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="font-medium">{item.original_filename}</p>
                        <p className="text-black/60">{item.evidence_type} | {item.source_type} | {item.ai_status}</p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button disabled={busy} onClick={() => updateEvidenceSource(item, "AGENT_ASSISTED")} className="focus-ring rounded-md border border-black/15 px-3 py-2 disabled:opacity-50">Assisted</button>
                        <button disabled={busy} onClick={() => updateEvidenceSource(item, "AGENT_VERIFIED")} className="focus-ring rounded-md border border-mint px-3 py-2 text-mint disabled:opacity-50">Verified</button>
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

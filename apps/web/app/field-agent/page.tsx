"use client";

import { useEffect, useState } from "react";
import { Upload, Wand2 } from "lucide-react";
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
      setSelected((current) => current ? data.find((item) => item.id === current.id) ?? data[0] ?? null : data[0] ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat kasus agen.");
    } finally {
      setLoading(false);
    }
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

  return (
    <Shell title="Dashboard Field Agent">
      {loading && <Loading />}
      {error && <ErrorMessage error={error} />}
      <div className="mt-5 grid gap-4 lg:grid-cols-[320px_1fr]">
        <aside className="rounded-md border border-black/10 bg-white p-4">
          <h2 className="font-semibold">Kasus dampingan</h2>
          <div className="mt-3 space-y-2">
            {profiles.map((profile) => (
              <button key={profile.id} onClick={() => setSelected(profile)} className={`focus-ring w-full rounded-md border px-3 py-2 text-left text-sm ${selected?.id === profile.id ? "border-mint bg-mint/5" : "border-black/10"}`}>
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
              <h2 className="text-xl font-semibold">{selected.business_name}</h2>
              <p className="mt-1 text-sm text-black/60">{selected.business_category} | {selected.status}</p>
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
            </>
          ) : (
            <p className="text-sm text-black/60">Belum ada kasus dampingan.</p>
          )}
        </section>
      </div>
    </Shell>
  );
}

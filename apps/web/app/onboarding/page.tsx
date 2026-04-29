"use client";

import { useEffect, useState } from "react";
import { Check, RotateCcw, Send, Trash2, Upload, XCircle } from "lucide-react";
import { apiFetch, emptyProfile } from "@/lib/api";
import type { BorrowerProfile, EvidenceItem, InstantCheck } from "@/types/api";
import { ResponsibleAIPanel } from "@/components/ResponsibleAIPanel";
import { ErrorMessage, Loading } from "@/components/State";
import { Shell } from "@/components/Shell";
import { WorkflowPanel } from "@/components/WorkflowPanel";

export default function OnboardingPage() {
  const [profile, setProfile] = useState<BorrowerProfile | null>(null);
  const [form, setForm] = useState<Partial<BorrowerProfile>>(emptyProfile);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [evidenceType, setEvidenceType] = useState("RECEIPT");
  const [file, setFile] = useState<File | null>(null);

  async function load() {
    const id = new URLSearchParams(window.location.search).get("id");
    if (!id) {
      setLoading(false);
      return;
    }
    try {
      const data = await apiFetch<BorrowerProfile>(`/borrower-profiles/${id}/`);
      setProfile(data);
      setForm(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat profil.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function profilePayload() {
    return {
      ...emptyProfile,
      ...form,
      business_name: String(form.business_name || "").trim() || "Profil UMKM Baru"
    };
  }

  async function ensureProfile() {
    if (profile) return profile;
    const data = await apiFetch<BorrowerProfile>("/borrower-profiles/", {
      method: "POST",
      body: JSON.stringify(profilePayload())
    });
    setProfile(data);
    setForm(data);
    window.history.replaceState(null, "", `/onboarding?id=${data.id}`);
    return data;
  }

  async function saveProfile() {
    setBusy(true);
    setError("");
    try {
      const body = JSON.stringify(profile ? form : profilePayload());
      const data = profile
        ? await apiFetch<BorrowerProfile>(`/borrower-profiles/${profile.id}/`, { method: "PATCH", body })
        : await apiFetch<BorrowerProfile>("/borrower-profiles/", { method: "POST", body });
      setProfile(data);
      setForm(data);
      window.history.replaceState(null, "", `/onboarding?id=${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan profil.");
    } finally {
      setBusy(false);
    }
  }

  async function consent() {
    setBusy(true);
    setError("");
    try {
      const currentProfile = await ensureProfile();
      await apiFetch(`/borrower-profiles/${currentProfile.id}/consent/`, { method: "POST", body: JSON.stringify({ consent_given: true }) });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menyimpan persetujuan.");
    } finally {
      setBusy(false);
    }
  }

  async function revokeConsent() {
    if (!profile || !window.confirm("Cabut persetujuan? Unggah bukti dan scoring akan diblokir sampai persetujuan diberikan lagi.")) return;
    setBusy(true);
    try {
      await apiFetch(`/borrower-profiles/${profile.id}/consent/`, { method: "POST", body: JSON.stringify({ consent_given: false }) });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mencabut persetujuan.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteProfile() {
    if (!profile || !window.confirm("Hapus profil usaha ini beserta bukti terkait?")) return;
    setBusy(true);
    try {
      await apiFetch(`/borrower-profiles/${profile.id}/`, { method: "DELETE" });
      setProfile(null);
      setForm(emptyProfile);
      window.history.replaceState(null, "", "/onboarding");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menghapus profil.");
    } finally {
      setBusy(false);
    }
  }

  async function uploadEvidence() {
    if (!profile || !file) return;
    setBusy(true);
    try {
      const formData = new FormData();
      formData.append("evidence_type", evidenceType);
      formData.append("source_type", "SELF_UPLOADED");
      formData.append("file", file);
      const item = await apiFetch<EvidenceItem>(`/borrower-profiles/${profile.id}/evidence/`, { method: "POST", body: formData });
      await apiFetch(`/evidence/${item.id}/process/`, { method: "POST", body: JSON.stringify({}) });
      await load();
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal mengunggah bukti.");
    } finally {
      setBusy(false);
    }
  }

  async function deleteEvidence(id: number) {
    if (!window.confirm("Hapus bukti ini?")) return;
    setBusy(true);
    try {
      await apiFetch(`/evidence/${id}/`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menghapus bukti.");
    } finally {
      setBusy(false);
    }
  }

  async function runCheck() {
    if (!profile) return;
    setBusy(true);
    try {
      const check = await apiFetch<InstantCheck>(`/borrower-profiles/${profile.id}/instant-check/`, { method: "POST", body: JSON.stringify({}) });
      setProfile({ ...profile, latest_instant_check: check });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal menjalankan Instant Evidence Check.");
    } finally {
      setBusy(false);
    }
  }

  async function submitAnalyst() {
    if (!profile) return;
    setBusy(true);
    try {
      const data = await apiFetch<BorrowerProfile>(`/borrower-profiles/${profile.id}/submit-to-analyst/`, { method: "POST", body: JSON.stringify({}) });
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Belum bisa dikirim ke analis.");
    } finally {
      setBusy(false);
    }
  }

  async function undoSubmitAnalyst() {
    if (!profile) return;
    setBusy(true);
    try {
      const data = await apiFetch<BorrowerProfile>(`/borrower-profiles/${profile.id}/undo-submit-to-analyst/`, { method: "POST", body: JSON.stringify({}) });
      setProfile(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal membatalkan pengiriman ke analis.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Shell title="Onboarding UMKM"><Loading /></Shell>;

  return (
    <Shell title="Onboarding Mandiri UMKM">
      {error && <ErrorMessage error={error} />}
      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_380px]">
        <section className="space-y-4">
          <Panel title="1. Mode onboarding">
            <div className="rounded-md border border-mint bg-mint/5 p-3 text-sm">Mode aktif: UMKM Self-Onboarding</div>
            {profile && (
              <div className="mt-3">
                <WorkflowPanel profile={profile} role="UMKM_OWNER" />
              </div>
            )}
          </Panel>
          <Panel title="2. Persetujuan data">
            <p className="text-sm text-black/65">Persetujuan wajib sebelum unggah bukti dan scoring. AI hanya membantu analisis, bukan keputusan pembiayaan.</p>
            {!profile && (
              <p className="mt-2 text-sm text-black/60">
                Jika belum ada profil, sistem akan membuat draft profil terlebih dahulu saat persetujuan disimpan.
              </p>
            )}
            <div className="mt-3 flex flex-wrap gap-2">
              <button disabled={busy || profile?.consent?.consent_given} onClick={consent} className="focus-ring inline-flex items-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                <Check size={16} /> {profile?.consent?.consent_given ? "Persetujuan tersimpan" : "Saya setuju"}
              </button>
              <button disabled={!profile?.consent?.consent_given || busy} onClick={revokeConsent} className="focus-ring inline-flex items-center gap-2 rounded-md border border-saffron px-3 py-2 text-sm font-medium text-saffron disabled:opacity-50">
                <XCircle size={16} /> Cabut Persetujuan
              </button>
            </div>
          </Panel>
          <Panel title="3. Profil usaha">
            <div className="grid gap-3 sm:grid-cols-2">
              <Input label="Nama usaha" value={form.business_name} onChange={(v) => setForm({ ...form, business_name: v })} />
              <Input label="Kategori" value={form.business_category} onChange={(v) => setForm({ ...form, business_category: v })} />
              <Input label="Lama usaha bulan" type="number" value={form.business_duration_months} onChange={(v) => setForm({ ...form, business_duration_months: Number(v) })} />
              <Input label="Jumlah diajukan" value={form.requested_amount} onChange={(v) => setForm({ ...form, requested_amount: v })} />
              <Input label="Estimasi omzet bulanan" value={form.estimated_monthly_revenue} onChange={(v) => setForm({ ...form, estimated_monthly_revenue: v })} />
              <Input label="Estimasi biaya bulanan" value={form.estimated_monthly_expense} onChange={(v) => setForm({ ...form, estimated_monthly_expense: v })} />
            </div>
            <TextArea label="Tujuan pembiayaan" value={form.financing_purpose} onChange={(v) => setForm({ ...form, financing_purpose: v })} />
            <TextArea label="Catatan arus kas sederhana" value={form.simple_cashflow_note} onChange={(v) => setForm({ ...form, simple_cashflow_note: v })} />
            <TextArea label="Catatan usaha" value={form.business_note} onChange={(v) => setForm({ ...form, business_note: v })} />
            <div className="mt-3 flex flex-wrap gap-2">
              <button disabled={busy} onClick={saveProfile} className="focus-ring rounded-md bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-50">Simpan profil</button>
              <button disabled={!profile || busy} onClick={deleteProfile} className="focus-ring inline-flex items-center gap-2 rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 disabled:opacity-50">
                <Trash2 size={16} /> Hapus Profil
              </button>
            </div>
          </Panel>
          <Panel title="4. Unggah bukti usaha">
            <div className="grid gap-3 sm:grid-cols-[180px_1fr_auto]">
              <select className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm" value={evidenceType} onChange={(event) => setEvidenceType(event.target.value)}>
                {["BUSINESS_PHOTO", "RECEIPT", "INVOICE", "SUPPLIER_NOTE", "SALES_NOTE", "QRIS_SCREENSHOT", "OTHER"].map((type) => <option key={type}>{type}</option>)}
              </select>
              <input className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm" type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
              <button disabled={!profile?.consent?.consent_given || !file || busy} onClick={uploadEvidence} className="focus-ring inline-flex items-center justify-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                <Upload size={16} /> Unggah
              </button>
            </div>
            <div className="mt-4 space-y-2">
              {(profile?.evidence_items ?? []).map((item) => (
                <div key={item.id} className="flex flex-col gap-2 rounded-md border border-black/10 p-3 text-sm sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-medium">{item.original_filename}</p>
                    <p className="text-black/60">{item.evidence_type} | {item.source_type} | {item.ai_status}</p>
                  </div>
                  <button disabled={busy} onClick={() => deleteEvidence(item.id)} className="focus-ring inline-flex items-center justify-center gap-2 rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 disabled:opacity-50">
                    <Trash2 size={16} /> Hapus
                  </button>
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="5. Instant Evidence Check">
            <button disabled={!profile?.consent?.consent_given || busy} onClick={runCheck} className="focus-ring rounded-md bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-50">Jalankan check</button>
            {profile?.latest_instant_check && <CheckResult check={profile.latest_instant_check} />}
            <div className="mt-3 flex flex-wrap gap-2">
              <button disabled={!profile?.latest_instant_check?.can_submit_to_analyst || busy} onClick={submitAnalyst} className="focus-ring inline-flex items-center gap-2 rounded-md bg-saffron px-3 py-2 text-sm font-medium text-white disabled:opacity-50">
                <Send size={16} /> Kirim ke analis
              </button>
              <button disabled={!profile || !["READY_FOR_ANALYST", "UNDER_REVIEW"].includes(profile.status) || busy} onClick={undoSubmitAnalyst} className="focus-ring inline-flex items-center gap-2 rounded-md border border-black/15 px-3 py-2 text-sm font-medium disabled:opacity-50">
                <RotateCcw size={16} /> Batalkan Kirim
              </button>
            </div>
          </Panel>
        </section>
        <ResponsibleAIPanel consentGiven={profile?.consent?.consent_given} />
      </div>
    </Shell>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="rounded-md border border-black/10 bg-white p-4"><h2 className="mb-3 font-semibold">{title}</h2>{children}</section>;
}

function Input({ label, value, onChange, type = "text" }: { label: string; value: unknown; onChange: (value: string) => void; type?: string }) {
  return <label className="text-sm font-medium">{label}<input type={type} className="focus-ring mt-1 w-full rounded-md border border-black/15 px-3 py-2" value={String(value ?? "")} onChange={(event) => onChange(event.target.value)} /></label>;
}

function TextArea({ label, value, onChange }: { label: string; value: unknown; onChange: (value: string) => void }) {
  return <label className="mt-3 block text-sm font-medium">{label}<textarea className="focus-ring mt-1 min-h-20 w-full rounded-md border border-black/15 px-3 py-2" value={String(value ?? "")} onChange={(event) => onChange(event.target.value)} /></label>;
}

function CheckResult({ check }: { check: InstantCheck }) {
  return (
    <div className="mt-3 rounded-md bg-paper p-3 text-sm">
      <p>Kelengkapan {check.data_completeness_score}% | Kualitas bukti {check.evidence_quality_score}%</p>
      <p className="mt-2 text-black/65">{check.business_note_summary}</p>
      <ul className="mt-2 list-disc pl-5">{check.recommended_next_steps.map((step) => <li key={step}>{step}</li>)}</ul>
    </div>
  );
}

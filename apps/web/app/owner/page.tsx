"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, Handshake, PlusCircle, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { BorrowerProfile } from "@/types/api";
import { ResponsibleAIPanel } from "@/components/ResponsibleAIPanel";
import { ErrorMessage, Loading } from "@/components/State";
import { Shell } from "@/components/Shell";

export default function OwnerDashboard() {
  const [profiles, setProfiles] = useState<BorrowerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [requestingAssist, setRequestingAssist] = useState(false);
  const [assistForm, setAssistForm] = useState({
    store_address: "",
    contact_phone: "",
    preferred_visit_time: "",
    assistance_note: ""
  });
  const [error, setError] = useState("");

  async function load() {
    try {
      setProfiles(await apiFetch<BorrowerProfile[]>("/borrower-profiles/"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const profile = profiles[0];
  const check = profile?.latest_instant_check;
  const canRequestAssist = !profile?.assisted_by_detail && (!profile || ["DRAFT", "CONSENTED", "EVIDENCE_UPLOADED", "NEEDS_COMPLETION"].includes(profile.status));

  async function requestFieldAgentAssist() {
    setRequestingAssist(true);
    setError("");
    try {
      const assistedProfile = await apiFetch<BorrowerProfile>("/borrower-profiles/request-field-agent-assist/", {
        method: "POST",
        body: JSON.stringify({
          profile_id: profile?.id,
          business_name: profile?.business_name,
          ...assistForm
        })
      });
      setProfiles([assistedProfile, ...profiles.filter((item) => item.id !== assistedProfile.id)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal meminta bantuan agen.");
    } finally {
      setRequestingAssist(false);
    }
  }

  return (
    <Shell title="Dashboard Pemilik UMKM">
      {loading && <Loading />}
      {error && <ErrorMessage error={error} />}
      {!loading && !profile && (
        <section className="mt-5 rounded-md border border-black/10 bg-white p-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-black/60">Belum ada profil usaha</p>
              <h2 className="mt-1 text-xl font-semibold">Mulai onboarding pertama</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-black/65">
                Buat profil usaha, berikan persetujuan, unggah bukti, lalu jalankan Instant Evidence Check.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Link
                href="/onboarding"
                className="focus-ring inline-flex items-center justify-center gap-2 rounded-md bg-mint px-4 py-2 text-sm font-medium text-white"
              >
                <PlusCircle size={17} /> Mulai Onboarding
              </Link>
            </div>
          </div>
          <AssistRequestForm
            values={assistForm}
            onChange={setAssistForm}
            onSubmit={requestFieldAgentAssist}
            busy={requestingAssist}
            title="Butuh bantuan agen?"
          />
        </section>
      )}
      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_360px]">
        {profile && (
          <section className="rounded-md border border-black/10 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm text-black/60">Status profil</p>
                <h2 className="text-xl font-semibold">{profile.business_name}</h2>
                <p className="mt-1 text-sm text-black/60">{profile.status}</p>
                {profile.assisted_by_detail && (
                  <p className="mt-1 text-sm text-mint">Dibantu oleh {profile.assisted_by_detail.full_name}</p>
                )}
              </div>
              <Link href={`/onboarding?id=${profile.id}`} className="focus-ring inline-flex items-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white">
                Lanjutkan <ArrowRight size={16} />
              </Link>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-3">
              <Metric label="Kelengkapan" value={`${check?.data_completeness_score ?? 0}%`} />
              <Metric label="Kualitas bukti" value={`${check?.evidence_quality_score ?? 0}%`} />
              <Metric label="Jumlah bukti" value={`${profile.evidence_count ?? 0}`} />
            </div>
            {check ? (
              <div className="mt-5 rounded-md bg-paper p-4 text-sm">
                <p className="font-medium">Instant Evidence Check terbaru</p>
                <p className="mt-2 text-black/65">{check.business_note_summary}</p>
                <ul className="mt-3 list-disc pl-5 text-black/70">{check.recommended_next_steps.map((step) => <li key={step}>{step}</li>)}</ul>
              </div>
            ) : (
              <div className="mt-5 flex items-center gap-2 rounded-md bg-paper p-4 text-sm text-black/60">
                <RefreshCw size={16} /> Instant Evidence Check belum dijalankan.
              </div>
            )}
            {canRequestAssist && (
              <AssistRequestForm
                values={assistForm}
                onChange={setAssistForm}
                onSubmit={requestFieldAgentAssist}
                busy={requestingAssist}
                title="Minta bantuan field agent untuk profil ini"
              />
            )}
          </section>
        )}
        <ResponsibleAIPanel consentGiven={profile?.consent?.consent_given} />
      </div>
    </Shell>
  );
}

function AssistRequestForm({
  values,
  onChange,
  onSubmit,
  busy,
  title
}: {
  values: { store_address: string; contact_phone: string; preferred_visit_time: string; assistance_note: string };
  onChange: (values: { store_address: string; contact_phone: string; preferred_visit_time: string; assistance_note: string }) => void;
  onSubmit: () => void;
  busy: boolean;
  title: string;
}) {
  return (
    <div className="mt-5 rounded-md border border-mint/30 bg-mint/5 p-4">
      <div className="flex items-center gap-2">
        <Handshake size={18} className="text-mint" />
        <h3 className="font-semibold">{title}</h3>
      </div>
      <p className="mt-1 text-sm text-black/65">
        Isi informasi kunjungan agar agen dapat datang ke lokasi usaha dan membantu melengkapi profil serta bukti.
      </p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <input
          className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm"
          placeholder="Alamat toko / patokan lokasi"
          value={values.store_address}
          onChange={(event) => onChange({ ...values, store_address: event.target.value })}
        />
        <input
          className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm"
          placeholder="Nomor kontak / WhatsApp"
          value={values.contact_phone}
          onChange={(event) => onChange({ ...values, contact_phone: event.target.value })}
        />
        <input
          className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm"
          placeholder="Waktu kunjungan yang diharapkan"
          value={values.preferred_visit_time}
          onChange={(event) => onChange({ ...values, preferred_visit_time: event.target.value })}
        />
        <input
          className="focus-ring rounded-md border border-black/15 px-3 py-2 text-sm"
          placeholder="Kebutuhan bantuan"
          value={values.assistance_note}
          onChange={(event) => onChange({ ...values, assistance_note: event.target.value })}
        />
      </div>
      <button
        disabled={busy}
        onClick={onSubmit}
        className="focus-ring mt-3 inline-flex items-center justify-center gap-2 rounded-md border border-mint bg-white px-4 py-2 text-sm font-medium text-mint disabled:opacity-50"
      >
        <Handshake size={17} /> {busy ? "Mengirim..." : "Minta Bantuan Agen"}
      </button>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-black/10 p-3">
      <p className="text-xs text-black/60">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { BorrowerProfile } from "@/types/api";
import { ResponsibleAIPanel } from "@/components/ResponsibleAIPanel";
import { Empty, ErrorMessage, Loading } from "@/components/State";
import { Shell } from "@/components/Shell";

export default function OwnerDashboard() {
  const [profiles, setProfiles] = useState<BorrowerProfile[]>([]);
  const [loading, setLoading] = useState(true);
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

  return (
    <Shell title="Dashboard Pemilik UMKM">
      {loading && <Loading />}
      {error && <ErrorMessage error={error} />}
      {!loading && !profile && <Empty text="Belum ada profil usaha. Mulai onboarding untuk membuat profil pertama." />}
      <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_360px]">
        {profile && (
          <section className="rounded-md border border-black/10 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm text-black/60">Status profil</p>
                <h2 className="text-xl font-semibold">{profile.business_name}</h2>
                <p className="mt-1 text-sm text-black/60">{profile.status}</p>
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
          </section>
        )}
        <ResponsibleAIPanel consentGiven={profile?.consent?.consent_given} />
      </div>
    </Shell>
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

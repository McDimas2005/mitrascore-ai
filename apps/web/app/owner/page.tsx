"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowRight, CheckCircle2, Clock3, FileText, Handshake, PlusCircle, RefreshCw } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { BorrowerProfile } from "@/types/api";
import { ResponsibleAIPanel } from "@/components/ResponsibleAIPanel";
import { ErrorMessage, Loading } from "@/components/State";
import { Shell } from "@/components/Shell";
import { VerificationReadinessPanel } from "@/components/VerificationReadinessPanel";
import { WorkflowPanel } from "@/components/WorkflowPanel";

const emptyAssistForm = {
  store_address: "",
  contact_phone: "",
  preferred_visit_time: "",
  assistance_note: ""
};

export default function OwnerDashboard() {
  const [profiles, setProfiles] = useState<BorrowerProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [requestingAssist, setRequestingAssist] = useState(false);
  const [assistForm, setAssistForm] = useState(emptyAssistForm);
  const [error, setError] = useState("");

  async function load() {
    try {
      const data = await apiFetch<BorrowerProfile[]>("/borrower-profiles/");
      setProfiles(data);
      setSelectedProfileId((current) => {
        if (current && data.some((item) => item.id === current)) return current;
        return data[0]?.id ?? null;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Gagal memuat dashboard.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const profile = profiles.find((item) => item.id === selectedProfileId) ?? profiles[0] ?? null;
  const check = profile?.latest_instant_check;
  const review = profile?.latest_review;
  const isFinalLocked = ["DECLINED", "APPROVED_FOR_FINANCING"].includes(review?.final_human_decision ?? "");
  const canRequestAssist = !profile?.assisted_by_detail && (
    !profile ||
    ["DRAFT", "CONSENTED", "EVIDENCE_UPLOADED", "NEEDS_COMPLETION"].includes(profile.status) ||
    ["NEEDS_MORE_DATA", "NOT_RECOMMENDED_AT_THIS_STAGE"].includes(review?.final_human_decision ?? "")
  );

  async function requestFieldAgentAssist(targetProfile: BorrowerProfile | null = profile) {
    setRequestingAssist(true);
    setError("");
    try {
      const assistedProfile = await apiFetch<BorrowerProfile>("/borrower-profiles/request-field-agent-assist/", {
        method: "POST",
        body: JSON.stringify({
          profile_id: targetProfile?.id,
          business_name: targetProfile?.business_name,
          ...assistForm
        })
      });
      setProfiles([assistedProfile, ...profiles.filter((item) => item.id !== assistedProfile.id)]);
      setSelectedProfileId(assistedProfile.id);
      setAssistForm(emptyAssistForm);
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
      {!loading && (
        <div className="mt-5 grid gap-4 xl:grid-cols-[300px_1fr_360px]">
          <aside className="rounded-md border border-black/10 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm text-black/60">Portofolio owner</p>
                <h2 className="font-semibold">Daftar usaha</h2>
              </div>
              <span className="rounded-md bg-paper px-2 py-1 text-xs font-medium text-black/60">{profiles.length}</span>
            </div>
            <Link
              href="/onboarding"
              className="focus-ring mt-4 inline-flex w-full items-center justify-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white"
            >
              <PlusCircle size={17} /> Tambah usaha
            </Link>
            {profiles.length ? (
              <div className="mt-4 space-y-2">
                {profiles.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setSelectedProfileId(item.id)}
                    className={`focus-ring w-full rounded-md border px-3 py-2 text-left text-sm ${
                      profile?.id === item.id ? "border-mint bg-mint/5" : "border-black/10 bg-white"
                    }`}
                  >
                    <span className="block font-medium">{item.business_name}</span>
                    <span className="mt-1 block text-black/60">{item.business_category || "Kategori belum diisi"}</span>
                    <span className="mt-1 block text-xs text-black/50">{item.workflow_stage?.label ?? item.status_label ?? item.status}</span>
                    {item.latest_review?.final_human_decision_label && (
                      <span className="mt-2 inline-flex rounded-md bg-paper px-2 py-1 text-xs font-medium text-black/65">
                        {item.latest_review.final_human_decision_label}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-sm leading-6 text-black/65">
                Belum ada usaha. Owner dapat membuat lebih dari satu profil usaha, masing-masing dengan bukti, review, dan keputusan sendiri.
              </p>
            )}
            {profiles.length > 0 && (
              <AssistRequestForm
                values={assistForm}
                onChange={setAssistForm}
                onSubmit={() => requestFieldAgentAssist(null)}
                busy={requestingAssist}
                title="Bantuan agen untuk usaha baru"
              />
            )}
          </aside>
          {profile ? (
          <section className="rounded-md border border-black/10 bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm text-black/60">Status profil</p>
                <h2 className="text-xl font-semibold">{profile.business_name}</h2>
                <p className="mt-1 text-sm text-black/60">{profile.status_label ?? profile.status}</p>
                {profile.assisted_by_detail && (
                  <p className="mt-1 text-sm text-mint">Dibantu oleh {profile.assisted_by_detail.full_name}</p>
                )}
              </div>
              {isFinalLocked ? (
                <div className="flex flex-col gap-2 sm:flex-row">
                  <span className="inline-flex items-center justify-center rounded-md border border-black/15 px-3 py-2 text-sm font-medium text-black/55">
                    Siklus selesai
                  </span>
                  <Link href="/onboarding" className="focus-ring inline-flex items-center justify-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white">
                    <PlusCircle size={16} /> Pengajuan baru
                  </Link>
                </div>
              ) : (
                <Link href={`/onboarding?id=${profile.id}`} className="focus-ring inline-flex items-center gap-2 rounded-md bg-mint px-3 py-2 text-sm font-medium text-white">
                  Lanjutkan <ArrowRight size={16} />
                </Link>
              )}
            </div>
            <div className="mt-5">
              <WorkflowPanel profile={profile} role="UMKM_OWNER" />
            </div>
            <div className="mt-5">
              <VerificationReadinessPanel profile={profile} />
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
            {review ? (
              <ReviewDecisionResult review={review} />
            ) : (
              ["READY_FOR_ANALYST", "UNDER_REVIEW"].includes(profile.status) && (
                <div className="mt-5 flex items-start gap-2 rounded-md border border-saffron/30 bg-saffron/5 p-4 text-sm text-black/70">
                  <Clock3 size={17} className="mt-0.5 shrink-0 text-saffron" />
                  <div>
                    <p className="font-medium text-black">Menunggu hasil review analis</p>
                    <p className="mt-1">Kasus sudah dikirim. Hasil keputusan manusia dan langkah lanjut akan muncul di sini setelah reviewer selesai.</p>
                  </div>
                </div>
              )
            )}
            {canRequestAssist && (
              <AssistRequestForm
                values={assistForm}
                onChange={setAssistForm}
                onSubmit={() => requestFieldAgentAssist(profile)}
                busy={requestingAssist}
                title="Minta bantuan field agent untuk profil ini"
              />
            )}
          </section>
          ) : (
            <section className="rounded-md border border-black/10 bg-white p-4">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-black/60">Belum ada profil usaha</p>
                  <h2 className="mt-1 text-xl font-semibold">Mulai onboarding pertama</h2>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-black/65">
                    Buat profil usaha, berikan persetujuan, unggah bukti, lalu jalankan Instant Evidence Check.
                  </p>
                </div>
                <Link
                  href="/onboarding"
                  className="focus-ring inline-flex items-center justify-center gap-2 rounded-md bg-mint px-4 py-2 text-sm font-medium text-white"
                >
                  <PlusCircle size={17} /> Mulai Onboarding
                </Link>
              </div>
              <AssistRequestForm
                values={assistForm}
                onChange={setAssistForm}
                onSubmit={() => requestFieldAgentAssist(null)}
                busy={requestingAssist}
                title="Butuh bantuan agen?"
              />
            </section>
          )}
          <ResponsibleAIPanel consentGiven={profile?.consent?.consent_given} />
        </div>
      )}
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
  const numeric = Number(value.replace("%", ""));
  const showProgress = value.endsWith("%") && Number.isFinite(numeric);
  return (
    <div className="rounded-md border border-black/10 p-3">
      <p className="text-xs text-black/60">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      {showProgress && (
        <div className="mt-2 h-2 rounded bg-black/10">
          <div className="h-2 rounded bg-mint" style={{ width: `${Math.max(0, Math.min(100, numeric))}%` }} />
        </div>
      )}
    </div>
  );
}

function ReviewDecisionResult({ review }: { review: BorrowerProfile["latest_review"] }) {
  if (!review) return null;
  const isDeclined = review.final_human_decision === "DECLINED";
  const reviewedAt = review.reviewed_at
    ? new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short" }).format(new Date(review.reviewed_at))
    : null;

  return (
    <div className={`mt-5 rounded-md border bg-white p-4 text-sm ${isDeclined ? "border-red-200" : "border-mint/30"}`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <CheckCircle2 size={18} className={isDeclined ? "text-red-700" : "text-mint"} />
            <p className="font-semibold">Hasil review manusia</p>
          </div>
          <p className={`mt-2 text-lg font-semibold ${isDeclined ? "text-red-800" : ""}`}>{review.final_human_decision_label}</p>
          <p className="mt-1 text-black/60">DeepScore {review.score}/100 | {review.readiness_band} | Confidence {review.confidence_level}</p>
          <p className="mt-2 rounded-md border border-saffron/40 bg-saffron/10 p-2 text-xs text-black/75">
            AI hanya mendukung analisis. Keputusan akhir pembiayaan tetap dilakukan oleh analis manusia.
          </p>
          {reviewedAt && <p className="mt-1 text-xs text-black/50">Diperbarui {reviewedAt}</p>}
        </div>
        <span className={`inline-flex w-fit items-center rounded-md px-2 py-1 text-xs font-medium ${isDeclined ? "bg-red-50 text-red-800" : "bg-paper text-black/70"}`}>
          {review.final_human_decision}
        </span>
      </div>
      {isDeclined && (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-red-900">
          <p className="font-medium">Pengajuan ditutup untuk siklus ini</p>
          <p className="mt-1 text-red-900/80">
            Owner tidak dapat mengubah profil, menambah bukti, menjalankan check ulang, atau mengirim ulang kasus ini dari jalur koreksi biasa.
          </p>
        </div>
      )}
      {review.analyst_notes && (
        <div className="mt-4 rounded-md bg-paper p-3">
          <div className="flex items-center gap-2 font-medium">
            <FileText size={16} className="text-mint" />
            Catatan reviewer
          </div>
          <p className="mt-2 text-black/70">{review.analyst_notes}</p>
        </div>
      )}
      <div className="mt-4">
        <p className="font-medium">Langkah lanjut</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-black/70">
          {review.follow_up_actions.map((action) => <li key={action}>{action}</li>)}
        </ul>
      </div>
      {review.suggested_next_action && !isDeclined && (
        <p className="mt-3 rounded-md border border-black/10 p-3 text-black/65">
          Rekomendasi DeepScore: {review.suggested_next_action}
        </p>
      )}
    </div>
  );
}

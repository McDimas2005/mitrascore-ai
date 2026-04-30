import { ShieldAlert, ShieldCheck } from "lucide-react";
import type { BorrowerProfile } from "@/types/api";

const sourceTypeLabels: Record<string, string> = {
  SELF_UPLOADED: "Unggahan owner",
  AGENT_ASSISTED: "Dibantu agen",
  AGENT_VERIFIED: "Diverifikasi agen"
};

const evidenceTypeLabels: Record<string, string> = {
  BUSINESS_PHOTO: "Foto usaha",
  RECEIPT: "Nota/struk",
  INVOICE: "Invoice",
  SUPPLIER_NOTE: "Catatan pemasok",
  SALES_NOTE: "Catatan penjualan",
  QRIS_SCREENSHOT: "QRIS",
  OTHER: "Lainnya"
};

const confidenceLabels: Record<string, string> = {
  LOW: "Low",
  MEDIUM: "Medium",
  HIGH: "High"
};

export function VerificationReadinessPanel({ profile }: { profile: BorrowerProfile }) {
  const readiness = profile.verification_readiness;
  if (!readiness) return null;
  const Icon = readiness.approval_ready ? ShieldCheck : ShieldAlert;

  return (
    <section className={`rounded-md border p-4 text-sm ${readiness.approval_ready ? "border-mint/30 bg-mint/5" : "border-saffron/40 bg-saffron/10"}`}>
      <div className="flex items-start gap-3">
        <Icon size={19} className={`mt-0.5 shrink-0 ${readiness.approval_ready ? "text-mint" : "text-saffron"}`} />
        <div className="min-w-0">
          <p className="font-semibold text-black">
            {readiness.approval_ready ? "Bukti kunci siap untuk approval" : "Belum siap approval: perlu verifikasi"}
          </p>
          <p className="mt-1 text-black/65">{readiness.policy_summary}</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            <Metric label="Keberadaan usaha" value={`${readiness.verified_business_presence_count}/${readiness.required_verified_business_presence_count}`} />
            <Metric label="Arus kas/transaksi" value={`${readiness.verified_cashflow_count}/${readiness.required_verified_cashflow_count}`} />
            <Metric label="Batas confidence" value={confidenceLabels[readiness.confidence_cap] ?? readiness.confidence_cap} />
          </div>
          {readiness.missing_requirements.length > 0 && (
            <div className="mt-3">
              <p className="font-medium">Yang perlu dilengkapi sebelum approval</p>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-black/70">
                {readiness.missing_requirements.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          )}
          {readiness.unverified_material_evidence.length > 0 && (
            <div className="mt-3">
              <p className="font-medium">Bukti kunci yang belum diverifikasi</p>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-black/70">
                {readiness.unverified_material_evidence.slice(0, 6).map((item) => (
                  <li key={item.id}>
                    {item.filename} ({evidenceTypeLabels[item.evidence_type] ?? item.evidence_type}, {sourceTypeLabels[item.source_type] ?? item.source_type})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-black/10 bg-white/70 p-2">
      <p className="text-xs text-black/55">{label}</p>
      <p className="mt-1 font-semibold text-black">{value}</p>
    </div>
  );
}

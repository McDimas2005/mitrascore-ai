import { ShieldAlert, ShieldCheck } from "lucide-react";
import type { BorrowerProfile } from "@/types/api";

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
            {readiness.approval_ready ? "Approval-ready evidence verification" : "Approval blocked: verification required"}
          </p>
          <p className="mt-1 text-black/65">{readiness.policy_summary}</p>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            <Metric label="Business presence" value={`${readiness.verified_business_presence_count}/${readiness.required_verified_business_presence_count}`} />
            <Metric label="Cashflow evidence" value={`${readiness.verified_cashflow_count}/${readiness.required_verified_cashflow_count}`} />
            <Metric label="Confidence cap" value={readiness.confidence_cap} />
          </div>
          {readiness.missing_requirements.length > 0 && (
            <div className="mt-3">
              <p className="font-medium">Required before approval</p>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-black/70">
                {readiness.missing_requirements.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          )}
          {readiness.unverified_material_evidence.length > 0 && (
            <div className="mt-3">
              <p className="font-medium">Unverified material evidence</p>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-black/70">
                {readiness.unverified_material_evidence.slice(0, 6).map((item) => (
                  <li key={item.id}>{item.filename} ({item.evidence_type}, {item.source_type})</li>
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

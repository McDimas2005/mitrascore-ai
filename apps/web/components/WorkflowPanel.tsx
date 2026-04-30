import { ClipboardList } from "lucide-react";
import type { BorrowerProfile, Role } from "@/types/api";

const roleLabels: Record<Role | "ADMIN", string> = {
  UMKM_OWNER: "UMKM owner",
  FIELD_AGENT: "Field agent",
  ANALYST: "Analis",
  ADMIN: "Admin"
};

export function WorkflowPanel({ profile, role }: { profile: BorrowerProfile; role: Role | "ADMIN" }) {
  const actions = profile.role_next_actions?.[role] ?? [];

  return (
    <section className="rounded-md border border-mint/30 bg-mint/5 p-4 text-sm">
      <div className="flex items-start gap-3">
        <ClipboardList size={19} className="mt-0.5 shrink-0 text-mint" />
        <div>
          <p className="font-semibold text-black">{profile.workflow_stage?.label ?? profile.status_label ?? profile.status}</p>
          <p className="mt-1 text-black/65">{profile.workflow_stage?.summary}</p>
          <p className="mt-2 text-xs font-medium uppercase text-black/50">Langkah berikutnya untuk {roleLabels[role]}</p>
          {actions.length ? (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-black/70">
              {actions.map((action) => <li key={action}>{action}</li>)}
            </ul>
          ) : (
            <p className="mt-2 text-black/60">Tidak ada aksi langsung saat ini.</p>
          )}
        </div>
      </div>
    </section>
  );
}

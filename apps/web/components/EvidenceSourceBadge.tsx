import type { EvidenceItem } from "@/types/api";

const badgeStyles: Record<string, string> = {
  SELF_UPLOADED: "border-black/15 bg-white text-black/70",
  AGENT_ASSISTED: "border-saffron/40 bg-saffron/10 text-black/75",
  AGENT_VERIFIED: "border-mint/40 bg-mint/10 text-mint"
};

export function EvidenceSourceBadge({ item }: { item: EvidenceItem }) {
  return (
    <span
      title={item.source_type_effect}
      className={`inline-flex w-fit items-center rounded-md border px-2 py-1 text-xs font-medium ${badgeStyles[item.source_type] ?? badgeStyles.SELF_UPLOADED}`}
    >
      {item.source_type_label ?? item.source_type}
    </span>
  );
}

export function EvidenceSourceDetails({ item }: { item: EvidenceItem }) {
  return (
    <div className="mt-2 rounded-md bg-paper p-2 text-xs leading-5 text-black/65">
      <p><span className="font-medium text-black/75">Meaning:</span> {item.source_type_summary}</p>
      <p><span className="font-medium text-black/75">Effect:</span> {item.source_type_effect}</p>
      {item.field_agent_note && <p><span className="font-medium text-black/75">Agent note:</span> {item.field_agent_note}</p>}
    </div>
  );
}

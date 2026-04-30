import { Info } from "lucide-react";

export function ActionAvailability({ reasons }: { reasons: Array<string | false | null | undefined> }) {
  const visibleReasons = Array.from(new Set(reasons.filter(Boolean) as string[]));
  if (!visibleReasons.length) return null;

  return (
    <div className="mt-3 rounded-md border border-saffron/30 bg-saffron/10 p-3 text-sm text-black/75">
      <div className="flex items-start gap-2">
        <Info size={16} className="mt-0.5 shrink-0 text-saffron" />
        <div>
          <p className="font-medium">Aksi belum tersedia</p>
          <ul className="mt-1 list-disc space-y-1 pl-5">
            {visibleReasons.map((reason, index) => (
              <li key={`${index}-${reason}`}>{reason}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

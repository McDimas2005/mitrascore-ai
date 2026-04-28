import type { Review } from "@/types/api";

export function ScoreCard({ review }: { review: Review }) {
  return (
    <section className="rounded-md border border-black/10 bg-white p-4">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-sm text-black/60">Credit Readiness Score</p>
          <p className="text-4xl font-semibold text-mint">{review.score}/100</p>
        </div>
        <div className="text-right text-sm">
          <p className="font-semibold">{review.readiness_band}</p>
          <p className="text-black/60">Confidence {review.confidence_level}</p>
        </div>
      </div>
      <div className="mt-4 space-y-2">
        {Object.entries(review.score_breakdown).map(([key, part]) => (
          <div key={key}>
            <div className="flex justify-between text-xs text-black/60">
              <span>{key.replaceAll("_", " ")}</span>
              <span>{part.score} x {part.weight}%</span>
            </div>
            <div className="mt-1 h-2 rounded bg-black/10">
              <div className="h-2 rounded bg-mint" style={{ width: `${part.score}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

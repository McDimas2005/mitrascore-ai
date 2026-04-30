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
      <p className="mt-3 rounded-md border border-saffron/40 bg-saffron/10 p-3 text-sm text-black/75">
        AI hanya mendukung analisis. Keputusan akhir pembiayaan tetap dilakukan oleh analis manusia.
      </p>
      <p className="mt-3 text-sm text-black/65">Confidence: {review.confidence_explanation}</p>
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
      <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
        <div className="rounded-md bg-paper p-3">
          <p className="font-medium">Data used</p>
          <ul className="mt-1 list-disc pl-5 text-black/70">{(review.data_used ?? []).map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
        <div className="rounded-md bg-paper p-3">
          <p className="font-medium">Data not used</p>
          <ul className="mt-1 list-disc pl-5 text-black/70">{(review.data_not_used ?? []).map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      </div>
    </section>
  );
}

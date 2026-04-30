export function Loading() {
  return <div className="mt-6 rounded-md border border-black/10 bg-white p-4 text-sm text-black/60">Memuat data...</div>;
}

export function Empty({ text }: { text: string }) {
  return <div className="mt-6 rounded-md border border-dashed border-black/20 bg-white p-4 text-sm text-black/60">{text}</div>;
}

export function ErrorMessage({ error }: { error: string }) {
  return <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>;
}

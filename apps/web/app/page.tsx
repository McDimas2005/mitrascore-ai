import Link from "next/link";
import { ArrowRight, ClipboardCheck, Handshake, LineChart } from "lucide-react";

const modes = [
  { title: "UMKM Self-Onboarding", text: "Pemilik usaha memberi persetujuan, mengisi profil, mengunggah bukti, lalu menjalankan Instant Evidence Check.", icon: ClipboardCheck },
  { title: "Assisted Field Agent", text: "Agen lapangan membantu melengkapi profil, menulis observasi, dan menandai bukti yang sudah diverifikasi.", icon: Handshake },
  { title: "Analyst DeepScore", text: "Analis melihat kasus terkirim, menjalankan skor berbasis aturan, dan mencatat keputusan manusia.", icon: LineChart }
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-paper">
      <section className="mx-auto flex min-h-[92vh] max-w-6xl flex-col justify-between px-4 py-8">
        <nav className="flex items-center justify-between">
          <span className="text-lg font-semibold text-mint">MitraScore AI</span>
          <Link href="/login" className="focus-ring inline-flex items-center gap-2 rounded-md bg-mint px-4 py-2 text-sm font-medium text-white">
            Login demo <ArrowRight size={16} />
          </Link>
        </nav>
        <div className="max-w-3xl">
          <h1 className="text-5xl font-semibold tracking-normal text-ink md:text-7xl">MitraScore AI</h1>
          <p className="mt-5 max-w-2xl text-xl text-black/70">From informal business evidence to explainable credit readiness.</p>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {modes.map((mode) => {
            const Icon = mode.icon;
            return (
              <article key={mode.title} className="rounded-md border border-black/10 bg-white p-4">
                <Icon className="text-mint" size={22} />
                <h2 className="mt-3 font-semibold">{mode.title}</h2>
                <p className="mt-2 text-sm leading-6 text-black/65">{mode.text}</p>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}

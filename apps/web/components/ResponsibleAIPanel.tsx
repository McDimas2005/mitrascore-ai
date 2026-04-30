import { ShieldCheck } from "lucide-react";

export function ResponsibleAIPanel({ consentGiven }: { consentGiven?: boolean }) {
  const dataUsed = ["Profil usaha", "Bukti yang diunggah", "Catatan agen", "Hasil OCR/ekstraksi bukti"];
  const dataNotUsed = ["Atribut sensitif", "Pengenalan wajah", "Media sosial", "Data kontak di luar unggahan"];
  const limitations = [
    "OCR dan Vision bisa keliru pada bukti buram, terpotong, tulisan tangan, atau pencahayaan rendah.",
    "Score adalah decision-support, bukan keputusan pembiayaan otomatis.",
    "Confidence LOW berarti bukti terbatas atau lemah; MEDIUM berarti cukup tetapi masih ada ketidakpastian; HIGH berarti bukti lengkap dan konsisten."
  ];
  return (
    <section className="mt-5 rounded-md border border-black/10 bg-white p-4">
      <div className="flex items-center gap-2">
        <ShieldCheck className="text-mint" size={20} />
        <h2 className="font-semibold">Panel Responsible AI</h2>
      </div>
      <div className="mt-4 grid gap-4 text-sm md:grid-cols-2">
        <div>
          <p className="font-medium">Status persetujuan: {consentGiven ? "Sudah diberikan" : "Belum diberikan"}</p>
          <p className="mt-2 font-medium">Data digunakan</p>
          <ul className="mt-1 list-disc pl-5 text-black/70">{dataUsed.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
        <div>
          <p className="font-medium">Data tidak digunakan</p>
          <ul className="mt-1 list-disc pl-5 text-black/70">{dataNotUsed.map((item) => <li key={item}>{item}</li>)}</ul>
          <p className="mt-3 rounded-md bg-saffron/10 p-3 text-saffron">
            AI tidak menyetujui atau menolak pembiayaan. Keputusan akhir wajib ditinjau manusia dan tercatat di audit log.
          </p>
        </div>
      </div>
      <div className="mt-4 rounded-md bg-paper p-3 text-sm">
        <p className="font-medium">Model limitations</p>
        <ul className="mt-1 list-disc pl-5 text-black/70">{limitations.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
    </section>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { login, setSession } from "@/lib/api";
import { ErrorMessage } from "@/components/State";

const demos = [
  ["UMKM", "umkm@mitrascore.demo"],
  ["Agen", "fieldagent@mitrascore.demo"],
  ["Analis", "analyst@mitrascore.demo"],
  ["Admin", "admin@mitrascore.demo"]
] as const;

export default function LoginPage() {
  const [email, setEmail] = useState("umkm@mitrascore.demo");
  const [password, setPassword] = useState("Demo123!");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const result = await login(email, password);
      setSession(result.access, result.refresh, result.user);
      const path = result.user.role === "ANALYST" || result.user.role === "ADMIN" ? "/analyst" : result.user.role === "FIELD_AGENT" ? "/field-agent" : "/owner";
      window.location.href = path;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login gagal.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-paper px-4">
      <section className="w-full max-w-md rounded-md border border-black/10 bg-white p-5">
        <Link href="/" className="focus-ring mb-4 inline-flex items-center gap-2 rounded-md border border-black/10 px-3 py-2 text-sm font-medium">
          <ArrowLeft size={16} /> Kembali
        </Link>
        <h1 className="text-2xl font-semibold">Login Demo</h1>
        <p className="mt-1 text-sm text-black/60">Gunakan salah satu akun demo. Password semua akun: Demo123!</p>
        <div className="mt-4 grid grid-cols-2 gap-2">
          {demos.map(([label, demoEmail]) => (
            <button key={demoEmail} className="focus-ring rounded-md border border-black/10 px-3 py-2 text-sm" onClick={() => setEmail(demoEmail)}>
              {label}
            </button>
          ))}
        </div>
        <form className="mt-5 space-y-3" onSubmit={submit}>
          <label className="block text-sm font-medium">
            Email
            <input className="focus-ring mt-1 w-full rounded-md border border-black/15 px-3 py-2" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label className="block text-sm font-medium">
            Password
            <input className="focus-ring mt-1 w-full rounded-md border border-black/15 px-3 py-2" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          {error && <ErrorMessage error={error} />}
          <button disabled={loading} className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-md bg-mint px-4 py-2 font-medium text-white disabled:opacity-60">
            {loading ? "Masuk..." : "Masuk"} <ArrowRight size={16} />
          </button>
        </form>
      </section>
    </main>
  );
}

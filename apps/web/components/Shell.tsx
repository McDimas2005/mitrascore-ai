"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowLeft, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { getRuntimeStatus, getUser, logout } from "@/lib/api";
import type { RuntimeStatus, User } from "@/types/api";

export function Shell({ children, title }: { children: React.ReactNode; title: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [runtime, setRuntime] = useState<RuntimeStatus | null>(null);
  const router = useRouter();

  useEffect(() => {
    setUser(getUser());
    getRuntimeStatus().then(setRuntime).catch(() => setRuntime(null));
  }, []);

  function fallbackPath() {
    if (user?.role === "FIELD_AGENT") return "/field-agent";
    if (user?.role === "ANALYST" || user?.role === "ADMIN") return "/analyst";
    if (user?.role === "UMKM_OWNER") return "/owner";
    return "/";
  }

  function goBack() {
    if (typeof window !== "undefined" && window.history.length > 1) {
      router.back();
      return;
    }
    router.push(fallbackPath());
  }

  return (
    <main className="min-h-screen bg-paper">
      <header className="border-b border-black/10 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link href="/" className="text-lg font-semibold text-mint">
            MitraScore AI
          </Link>
          <div className="flex items-center gap-3 text-sm">
            {user && <span className="hidden text-black/60 sm:inline">{user.full_name}</span>}
            <button
              className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-md border border-black/10 bg-white"
              title="Keluar"
              onClick={() => {
                logout();
                window.location.href = "/login";
              }}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </header>
      <section className="mx-auto max-w-6xl px-4 py-6">
        {runtime && <ModeBanner runtime={runtime} />}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-2xl font-semibold">{title}</h1>
          <button
            className="focus-ring inline-flex items-center justify-center gap-2 rounded-md border border-black/10 bg-white px-3 py-2 text-sm font-medium"
            onClick={goBack}
          >
            <ArrowLeft size={16} /> Kembali
          </button>
        </div>
        {children}
      </section>
    </main>
  );
}

function ModeBanner({ runtime }: { runtime: RuntimeStatus }) {
  const isMock = runtime.ai_mode === "mock";
  return (
    <div className={`mb-4 rounded-md border p-3 text-sm ${isMock ? "border-saffron/40 bg-saffron/10" : "border-mint/40 bg-mint/5"}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="font-medium">
          {isMock ? "Synthetic demo mode aktif" : "Azure AI mode aktif"} · File storage: {runtime.storage_mode === "azure_blob" ? "Azure Blob private container" : "Local storage"}
        </p>
        <p className="text-black/65">
          {runtime.responsible_ai_notice}
        </p>
      </div>
    </div>
  );
}

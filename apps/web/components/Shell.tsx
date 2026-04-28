"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { getUser, logout } from "@/lib/api";
import type { User } from "@/types/api";

export function Shell({ children, title }: { children: React.ReactNode; title: string }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

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
        <h1 className="text-2xl font-semibold">{title}</h1>
        {children}
      </section>
    </main>
  );
}

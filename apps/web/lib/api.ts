import type { BorrowerProfile, RuntimeStatus, User } from "@/types/api";

function apiBase() {
  const configured = process.env.NEXT_PUBLIC_API_URL || "";
  let origin = configured.replace(/\/$/, "");
  if (!origin && typeof window !== "undefined" && ["localhost", "127.0.0.1"].includes(window.location.hostname)) {
    origin = `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  if (!origin) {
    throw new Error("NEXT_PUBLIC_API_URL is required outside local development.");
  }
  return origin.endsWith("/api") ? origin : `${origin}/api`;
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("accessToken");
}

export function setSession(access: string, refresh: string, user: User) {
  window.localStorage.setItem("accessToken", access);
  window.localStorage.setItem("refreshToken", refresh);
  window.localStorage.setItem("user", JSON.stringify(user));
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem("user");
  return raw ? (JSON.parse(raw) as User) : null;
}

export function logout() {
  window.localStorage.removeItem("accessToken");
  window.localStorage.removeItem("refreshToken");
  window.localStorage.removeItem("user");
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${apiBase()}${path}`, { ...options, headers });
  if (response.status === 204) return undefined as T;
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: "Terjadi kesalahan." }));
    throw new Error(detail.detail || JSON.stringify(detail));
  }
  return response.json() as Promise<T>;
}

export async function login(email: string, password: string) {
  const response = await fetch(`${apiBase()}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!response.ok) throw new Error("Login gagal. Periksa kredensial demo.");
  return response.json() as Promise<{ access: string; refresh: string; user: User }>;
}

export async function getRuntimeStatus() {
  const response = await fetch(`${apiBase()}/runtime-status/`);
  if (!response.ok) throw new Error("Gagal memuat status runtime.");
  return response.json() as Promise<RuntimeStatus>;
}

export const emptyProfile: Partial<BorrowerProfile> = {
  business_name: "",
  business_category: "Warung sembako",
  business_duration_months: 12,
  financing_purpose: "",
  requested_amount: "5000000",
  estimated_monthly_revenue: "10000000",
  estimated_monthly_expense: "7500000",
  simple_cashflow_note: "",
  business_note: ""
};

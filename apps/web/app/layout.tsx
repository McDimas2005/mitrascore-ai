import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MitraScore AI",
  description: "From informal business evidence to explainable credit readiness."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}

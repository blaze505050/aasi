import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AASI — Autonomous Aerospace Scientific Intelligence",
  description: "Experimental AI research assistant for aerospace engineering & space science.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

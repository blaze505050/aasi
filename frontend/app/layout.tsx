import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AASI — Autonomous Aerospace Scientific Intelligence",
  description:
    "AI-powered scientific investigation platform for aerospace engineering. Real CFD computation, multi-fidelity analysis, and epistemic validation.",
  keywords: [
    "aerospace",
    "CFD",
    "computational fluid dynamics",
    "NACA",
    "aerodynamics",
    "scientific computing",
    "OpenFOAM",
  ],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>{children}</body>
    </html>
  );
}

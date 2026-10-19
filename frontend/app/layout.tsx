import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AASI — Autonomous Aerospace Scientific Intelligence",
  description:
    "Production-grade aerodynamic engineering intelligence platform. Deterministic panel solver computations, ASME V&V 20-2009 verification, multi-fidelity surrogate models, and cryptographic provenance for aerospace design workflows.",
  keywords: [
    "aerospace engineering",
    "CFD",
    "computational fluid dynamics",
    "NACA airfoil",
    "aerodynamics",
    "scientific computing",
    "OpenFOAM",
    "panel method",
    "ASME V&V 20",
    "flight envelope",
    "USAF DATCOM",
    "aerodynamic database",
    "surrogate model",
    "neural operator",
    "aerospace AI",
  ],
  authors: [
    { name: "AASI Engineering", url: "https://github.com/blaze505050/aasi" },
  ],
  creator: "Project Polaris",
  publisher: "Project Polaris",
  robots: { index: true, follow: true },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://aasi.projectpolaris.in",
    siteName: "AASI — Autonomous Aerospace Scientific Intelligence",
    title: "AASI — Autonomous Aerospace Scientific Intelligence",
    description:
      "Deterministic aerodynamic database generation, ASME V&V 20 verification, and multi-fidelity investigation platform for aerospace engineers.",
  },
  twitter: {
    card: "summary_large_image",
    title: "AASI — Autonomous Aerospace Scientific Intelligence",
    description:
      "Production aerospace engineering intelligence: panel solvers, polar sweeps, and cryptographic verification.",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#070a12",
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
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <meta name="application-name" content="AASI" />
        <meta name="apple-mobile-web-app-title" content="AASI" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </head>
      <body>{children}</body>
    </html>
  );
}

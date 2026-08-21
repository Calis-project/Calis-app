import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Calis AI Experiment Harness",
  description: "Compare text, VLM, CV, and hybrid coaching analysis paths.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

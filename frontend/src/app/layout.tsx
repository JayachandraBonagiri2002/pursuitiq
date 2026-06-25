import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "PursuitIQ — Agentic Pursuit Intelligence",
  description: "HCLTech × OpenAI Hackathon | 6 AI agents. 12 minutes. Win more deals.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased min-h-screen`} style={{ background: "#09090f" }}>
        {children}
      </body>
    </html>
  );
}

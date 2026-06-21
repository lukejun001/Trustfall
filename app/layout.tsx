import "./globals.css";
import type { Metadata } from "next";
export const metadata: Metadata = { title: "Trustfall · Terac", description: "Human-labeled scam safety data collection" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }

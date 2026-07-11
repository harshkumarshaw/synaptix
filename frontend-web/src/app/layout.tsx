import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster as SonnerToaster } from "@/components/ui/sonner";
import { Toaster as ToastToaster } from "@/components/ui/toaster";
import { QueryProvider } from "@/components/providers/query-provider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Synaptix — Academic Operations Platform",
  description: "NMC CBME compliant academic management for JMN Medical College",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <QueryProvider>
          {children}
          <SonnerToaster />
          <ToastToaster />
        </QueryProvider>
      </body>
    </html>
  );
}

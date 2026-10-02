import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import Header from "@/components/layout/header";

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AUSSIZ-ISMS',
  description: 'AUSSIZ Internal Student Management System',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.className}>
      <body>
        <Header />
        <main className="flex min-h-screen flex-col">
          {children}
        </main>
      </body>
    </html>
  );
}
import type { Metadata } from "next";
import { AuthProvider } from "@/context/AuthContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "Personal OS",
  description: "Personal AI-powered operating system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-surface-0 text-content-primary antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
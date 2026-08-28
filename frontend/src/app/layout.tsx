import type { Metadata, Viewport } from "next";
import { AuthProvider } from "@/context/AuthContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "Personal OS",
  description: "Personal AI-powered operating system",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Personal OS",
  },
  formatDetection: {
    telephone: false,
  },
};

export const viewport: Viewport = {
  themeColor: "#07080a",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-surface-0 text-content-primary antialiased selection:bg-brand selection:text-white">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
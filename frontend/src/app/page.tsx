"use client";

import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function HomePage() {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-0">
        <div className="text-content-secondary text-sm animate-pulse">
          Loading Personal OS...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Avoid flashing protected content during redirect
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-surface-0 p-6">
      <div className="w-full max-w-lg rounded-xl border border-border-subtle bg-surface-1 p-8 shadow-2xl">
        <div className="flex items-center justify-between border-b border-border-subtle pb-4 mb-6">
          <div>
            <h1 className="text-xl font-bold text-content-primary">Personal OS</h1>
            <p className="text-xs text-content-secondary">Workspace v1.0</p>
          </div>
          <span className="inline-flex items-center rounded-full bg-type-grocery/10 px-2.5 py-0.5 text-xs font-medium text-type-grocery">
            Authenticated
          </span>
        </div>

        <div className="space-y-4">
          <p className="text-sm text-content-secondary">
            Welcome inside! Login successfully kaam kar raha hai. Access token memory mein hai aur refresh token HttpOnly cookie mein secure hai.
          </p>

          <div className="rounded-lg bg-surface-2 p-4 border border-border-subtle">
            <p className="text-xs font-mono text-content-tertiary">
              Status: Ready for Inbox & Chat UI (Session 12)
            </p>
          </div>

          <button
            onClick={logout}
            className="w-full rounded bg-surface-3 p-3 text-sm font-semibold text-content-primary transition hover:bg-danger hover:text-white"
          >
            Log Out
          </button>
        </div>
      </div>
    </main>
  );
}
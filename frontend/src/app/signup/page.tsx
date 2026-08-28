"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await apiFetch("/auth/sign-up", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      });

      // Redirect to login page upon successful registration
      router.push("/login?registered=true");
    } catch (err: any) {
      setError(err.message || "Registration failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-0 px-4">
      <div className="w-full max-w-md rounded-lg border border-border-subtle bg-surface-1 p-8 shadow-xl">
        <h2 className="mb-2 text-2xl font-bold text-content-primary">Create Account</h2>
        <p className="mb-6 text-sm text-content-secondary">Get started with your Personal OS</p>

        {error && (
          <div className="mb-4 rounded border border-danger/20 bg-danger/10 p-3 text-sm text-danger">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-content-secondary mb-1">
             Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded border border-border-subtle bg-surface-2 p-3 text-content-primary placeholder-content-tertiary focus:border-brand focus:outline-none"
              placeholder="John Deo"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-content-secondary mb-1">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded border border-border-subtle bg-surface-2 p-3 text-content-primary placeholder-content-tertiary focus:border-brand focus:outline-none"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-content-secondary mb-1">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded border border-border-subtle bg-surface-2 p-3 text-content-primary placeholder-content-tertiary focus:border-brand focus:outline-none"
              placeholder="Min 8 characters"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded bg-brand p-3 font-semibold text-content-primary transition hover:bg-brand/90 disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Sign Up"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-content-secondary">
          Already have an account?{" "}
          <Link href="/login" className="text-brand hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
"use client";

import { useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { HeartPulse, LoaderCircle, TriangleAlert } from "lucide-react";
import Link from "next/link";
import { registerAction } from "@/app/actions";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (username.trim().length < 3) {
      setError("Username must be at least 3 characters.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);

    try {
      const result = await registerAction(username, password);
      if (result.error) {
        setError(result.error);
      } else {
        router.push("/login");
      }
    } catch (err) {
      setError("An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
      <Link
        href="/"
        className="absolute left-6 top-6 inline-flex items-center gap-1.5 rounded-full bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] px-4 py-2 text-sm font-semibold !text-white shadow-lg shadow-teal-900/15 transition-transform hover:-translate-y-0.5"
      >
        <ArrowLeft className="size-4" />
        Home
      </Link>
      <div className="w-full max-w-md rounded-[2rem] border border-white/70 bg-white/75 p-8 shadow-2xl shadow-teal-950/8 backdrop-blur-sm sm:p-12">
        <div className="mb-8 flex items-center justify-center gap-3">
          <HeartPulse className="h-10 w-10 text-[var(--primary)]" />
          <span
            className="text-3xl font-bold tracking-tight"
            style={{
              fontFamily: "'Manrope', sans-serif",
              color: "var(--primary)",
            }}
          >
            Aarohi
          </span>
        </div>

        <h1 className="mb-2 text-center text-2xl font-semibold tracking-tight">
          Register Clinic
        </h1>
        <p className="mb-8 text-center text-sm text-black/60">
          Create a new clinic account for AI patient intake.
        </p>

        {error ? (
          <div className="mb-6 flex items-start gap-3 rounded-[1.25rem] border border-rose-200 bg-rose-50 px-4 py-3 text-left text-sm text-rose-700">
            <TriangleAlert className="mt-0.5 size-4 shrink-0" />
            <p>{error}</p>
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label
              htmlFor="username"
              className="mb-2 block text-sm font-medium text-black/70"
            >
              Clinic ID
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-[var(--surface-low)] px-4 py-3 outline-none focus:border-[var(--primary)]"
              placeholder="e.g. myclinic"
              required
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="mb-2 block text-sm font-medium text-black/70"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-[var(--surface-low)] px-4 py-3 outline-none focus:border-[var(--primary)]"
              placeholder="At least 6 characters"
              required
            />
          </div>
          <div>
            <label
              htmlFor="confirmPassword"
              className="mb-2 block text-sm font-medium text-black/70"
            >
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-xl border border-black/10 bg-[var(--surface-low)] px-4 py-3 outline-none focus:border-[var(--primary)]"
              placeholder="Repeat password"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-full bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] py-3.5 font-semibold text-white shadow-xl shadow-teal-900/15 transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-80"
          >
            {loading ? (
              <LoaderCircle className="size-5 animate-spin" />
            ) : (
              "Create Account"
            )}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-black/50">
          Already have an account?{" "}
          <Link href="/login" className="font-semibold text-[var(--primary)] hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </main>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { HeartPulse, LoaderCircle, TriangleAlert } from "lucide-react";
import { loginAction } from "@/app/actions";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const result = await loginAction(username, password);
      if (result.error) {
        setError(result.error);
      } else {
        router.push("/intake");
      }
    } catch (err) {
      setError("An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-6 text-foreground">
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
          Clinic Login
        </h1>
        <p className="mb-8 text-center text-sm text-black/60">
          Sign in to access your AI patient intake portal.
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
              "Sign In"
            )}
          </button>
        </form>
      </div>
    </main>
  );
}

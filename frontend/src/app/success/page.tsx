"use client";

import { useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  HeartPulse,
  Home,
  ShieldCheck,
  UserRoundCheck,
} from "lucide-react";

const SUCCESS_STORAGE_KEY = "aarohi-intake-summary";

const detailLabels: Record<string, string> = {
  patient_name: "Full Name",
  age: "Age",
  gender: "Gender",
  chief_complaint: "Chief Complaint",
  symptom_duration: "Symptom Duration",
  severity_score: "Severity",
  known_conditions: "Known Conditions",
  current_medications: "Current Medications",
};

const nextSteps = [
  {
    icon: ShieldCheck,
    title: "Data Verified",
    description: "Your intake details have been securely captured and finalized.",
  },
  {
    icon: UserRoundCheck,
    title: "Clinician Review",
    description: "The care team can now review your symptoms before consultation.",
  },
  {
    icon: HeartPulse,
    title: "Ready for Consultation",
    description: "You are set for the next step in the clinical flow.",
  },
];

export default function SuccessPage() {
  const [summary] = useState<Record<string, string>>(() => {
    if (typeof window === "undefined") {
      return {};
    }

    const raw = sessionStorage.getItem(SUCCESS_STORAGE_KEY);
    if (!raw) {
      return {};
    }

    try {
      return JSON.parse(raw) as Record<string, string>;
    } catch {
      return {};
    }
  });

  const summaryEntries = Object.entries(summary).filter(([, value]) => value);

  return (
    <main className="min-h-screen bg-background text-foreground">
      <nav className="glass sticky top-0 z-50 flex items-center justify-between px-6 py-4 sm:px-10">
        <Link
          href="/"
          className="group flex items-center gap-3 transition-opacity hover:opacity-85"
        >
          <div className="flex items-center gap-2">
            <HeartPulse className="w-7 h-7 text-[var(--primary)]" />
            <span
              className="text-xl font-bold tracking-tight"
              style={{
                fontFamily: "'Manrope', sans-serif",
                color: "var(--primary)",
              }}
            >
              Aarohi
            </span>
          </div>
        </Link>

        <Link
          href="/"
          className="rounded-full border border-black/10 bg-white/80 px-4 py-2 text-sm font-semibold text-black/65 shadow-sm"
        >
          Home
        </Link>
      </nav>

      <section className="flex min-h-[calc(100vh-80px)] items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-3xl rounded-[2rem] border border-white/70 bg-white/80 p-8 text-center shadow-2xl shadow-teal-950/8 backdrop-blur-sm sm:p-12">
          <div className="mx-auto flex size-24 items-center justify-center rounded-full bg-[var(--primary-fixed)] text-[var(--primary-container)] shadow-inner animate-bounce [animation-duration:2s]">
            <CheckCircle2 className="size-11" />
          </div>

          <h1
            className="mt-7 text-4xl tracking-[-0.03em] sm:text-5xl"
            style={{ fontFamily: "var(--font-manrope), sans-serif" }}
          >
            Registration Completed Successfully
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-base leading-8 text-black/60 sm:text-lg">
            Aarohi has finished your intake and the session is complete. Your
            information is ready for the next clinical step.
          </p>

          {summaryEntries.length > 0 ? (
            <div className="mt-8 rounded-[1.75rem] bg-white p-5 text-left shadow-sm sm:p-7">
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[var(--primary)]">
                Confirmed Intake Details
              </p>
              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                {summaryEntries.map(([key, value]) => (
                  <div
                    key={key}
                    className="rounded-[1.25rem] border border-black/6 bg-[var(--surface-low)] p-4"
                  >
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-black/45">
                      {detailLabels[key] ?? key}
                    </p>
                    <p className="mt-2 text-sm leading-7 text-black/72">
                      {value}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="mt-10 rounded-[1.75rem] bg-[var(--surface-low)] p-5 text-left sm:p-7">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-[var(--primary)]">
              What Happens Next
            </p>
            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              {nextSteps.map((step) => {
                const Icon = step.icon;
                return (
                  <div
                    key={step.title}
                    className="rounded-[1.25rem] bg-white p-5 shadow-sm"
                  >
                    <div className="flex size-11 items-center justify-center rounded-2xl bg-[var(--primary-fixed)] text-[var(--primary-container)]">
                      <Icon className="size-5" />
                    </div>
                    <h2 className="mt-4 text-lg font-semibold tracking-tight">
                      {step.title}
                    </h2>
                    <p className="mt-2 text-sm leading-7 text-black/58">
                      {step.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>

          <Link
            href="/"
            className="mt-8 inline-flex items-center gap-2 rounded-full bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] px-7 py-3.5 text-base font-semibold !text-white shadow-xl shadow-teal-900/15 transition-transform hover:-translate-y-0.5 [text-shadow:0_1px_1px_rgba(0,62,62,0.28)]"
          >
            <Home className="size-4" />
            Back to Home
          </Link>
        </div>
      </section>
    </main>
  );
}

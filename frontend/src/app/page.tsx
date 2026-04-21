"use client";

import Link from "next/link";
import {
  ArrowRight,
  Brain,
  Clock3,
  HeartPulse,
  Languages,
  Mic,
  ShieldCheck,
  Stethoscope,
  Waves,
} from "lucide-react";

const features = [
  {
    icon: Languages,
    title: "Multilingual Support",
    description:
      "Aarohi understands Hindi, Hinglish, and English, making patient intake more natural and accessible.",
  },
  {
    icon: Clock3,
    title: "24/7 Availability",
    description:
      "The assistant stays ready for registration at any hour, reducing front-desk load and patient wait time.",
  },
  {
    icon: ShieldCheck,
    title: "Secure AI Extraction",
    description:
      "Structured details are captured and synced from the backend in real time for reliable intake review.",
  },
  {
    icon: Mic,
    title: "Voice-First Experience",
    description:
      "Patients can talk naturally, while text chat remains available as a fallback for accessibility and noisy spaces.",
  },
  {
    icon: Stethoscope,
    title: "Clinical Accuracy",
    description:
      "The flow collects the key intake details needed for triage and clinician preparation before consultation.",
  },
  {
    icon: Brain,
    title: "Real-Time Dashboard",
    description:
      "Backend extraction updates flow live during the session, ready to power future structured dashboards.",
  },
];

const steps = [
  {
    title: "Connect",
    description: "Begin a secure session with Aarohi directly in the browser.",
  },
  {
    title: "Converse",
    description: "Speak naturally or type your responses while Aarohi guides the intake.",
  },
  {
    title: "Complete",
    description: "Finish registration and move smoothly into clinician review.",
  },
];

export default function HomePage() {
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
          href="https://github.com/tanishra/aarohi"
          className="inline-flex items-center gap-2 rounded-full bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] px-5 py-2.5 text-sm font-semibold !text-white shadow-lg shadow-teal-900/15 transition-transform hover:-translate-y-0.5 [text-shadow:0_1px_1px_rgba(0,62,62,0.32)]"
        >
          GitHub
          <ArrowRight className="size-4" />
        </Link>
      </nav>

      <section className="relative overflow-hidden px-6 pb-16 pt-16 sm:px-10 sm:pb-24 sm:pt-24">
        <div
          className="absolute -left-32 -top-32 h-96 w-96 rounded-full opacity-20 blur-3xl"
          style={{ background: "var(--primary-fixed)" }}
        />
        <div
          className="absolute -bottom-32 -right-32 h-96 w-96 rounded-full opacity-15 blur-3xl"
          style={{ background: "var(--primary)" }}
        />

        <div className="relative mx-auto flex max-w-6xl flex-col gap-10">
          <div className="max-w-4xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-black/8 bg-white/80 px-4 py-2 text-sm font-medium text-black/65 shadow-sm">
              <Waves className="size-4 text-[var(--primary)]" />
              Voice-native patient registration
            </span>

            <h1
              className="mt-6 text-5xl leading-[0.95] tracking-[-0.04em] sm:text-7xl"
              style={{ fontFamily: "var(--font-manrope), sans-serif" }}
            >
              The Future of{" "}
              <span style={{ color: "var(--primary-container)" }}>
                Patient Intake
              </span>
            </h1>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-black/65 sm:text-xl">
              Aarohi brings a calm, AI-guided intake experience to the clinic
              flow, combining real-time conversation, structured extraction,
              and a human-friendly avatar interface.
            </p>

            <div className="mt-10 flex flex-col gap-4 sm:flex-row">
              <Link
                href="/intake"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[linear-gradient(135deg,var(--primary),var(--primary-container))] px-7 py-3.5 text-base font-semibold !text-white shadow-xl shadow-teal-900/15 transition-transform hover:-translate-y-0.5 [text-shadow:0_1px_1px_rgba(0,62,62,0.32)]"
              >
                Start Registration Now
                <ArrowRight className="size-4" />
              </Link>
              <a
                href="#features"
                className="inline-flex items-center justify-center rounded-full border border-black/10 bg-white/80 px-7 py-3.5 text-base font-semibold text-black/70 shadow-sm transition-colors hover:bg-white"
              >
                Explore Features
              </a>
            </div>
          </div>

          <div className="grid gap-4 rounded-[2rem] border border-white/70 bg-white/70 p-4 shadow-xl shadow-teal-950/5 backdrop-blur-sm sm:grid-cols-3 sm:p-6">
            {[
              { val: "8+", label: "Data Fields" },
              { val: "99%", label: "Accuracy" },
              { val: "< 3min", label: "Avg Session" },
            ].map((stat) => (
              <div
                key={stat.label}
                className="rounded-[1.5rem] bg-white px-6 py-7 text-center shadow-sm"
              >
                <p className="text-3xl font-semibold tracking-tight text-[var(--primary-container)]">
                  {stat.val}
                </p>
                <p className="mt-2 text-sm uppercase tracking-[0.22em] text-black/45">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="px-6 py-18 sm:px-10">
        <div className="mx-auto max-w-6xl">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[var(--primary)]">
              Capabilities
            </p>
            <h2
              className="mt-4 text-4xl tracking-[-0.03em] sm:text-5xl"
              style={{ fontFamily: "var(--font-manrope), sans-serif" }}
            >
              Built for modern intake, not just another form.
            </h2>
          </div>

          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <article
                  key={feature.title}
                  className="rounded-[1.75rem] border border-black/6 bg-white p-6 shadow-sm transition-transform duration-200 hover:-translate-y-1"
                >
                  <div className="flex size-12 items-center justify-center rounded-2xl bg-[var(--primary-fixed)] text-[var(--primary-container)]">
                    <Icon className="size-5" />
                  </div>
                  <h3 className="mt-5 text-xl font-semibold tracking-tight">
                    {feature.title}
                  </h3>
                  <p className="mt-3 text-sm leading-7 text-black/62">
                    {feature.description}
                  </p>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="px-6 py-18 sm:px-10">
        <div className="mx-auto max-w-6xl rounded-[2rem] bg-[var(--surface-low)] px-6 py-10 sm:px-10 sm:py-14">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[var(--primary)]">
            How It Works
          </p>
          <div className="mt-8 grid gap-5 lg:grid-cols-3">
            {steps.map((step, index) => (
              <div
                key={step.title}
                className="rounded-[1.5rem] bg-white px-6 py-7 shadow-sm"
              >
                <div className="flex size-11 items-center justify-center rounded-full bg-[var(--primary-fixed)] text-sm font-semibold text-[var(--primary-container)]">
                  0{index + 1}
                </div>
                <h3 className="mt-5 text-2xl font-semibold tracking-tight">
                  {step.title}
                </h3>
                <p className="mt-3 text-sm leading-7 text-black/60">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="px-6 pb-20 pt-6 sm:px-10">
        <div
          className="mx-auto flex max-w-6xl flex-col items-start gap-5 rounded-[2rem] px-8 py-10 text-white shadow-2xl shadow-teal-950/15 sm:flex-row sm:items-center sm:justify-between"
          style={{
            background:
              "linear-gradient(135deg, var(--primary), var(--primary-container))",
          }}
        >
          <div className="max-w-2xl">
            <p className="text-sm uppercase tracking-[0.22em] text-white/70">
              Start Now
            </p>
            <h2
              className="mt-3 text-3xl tracking-[-0.03em] sm:text-4xl"
              style={{ fontFamily: "var(--font-manrope), sans-serif" }}
            >
              Bring empathy, structure, and speed to patient registration.
            </h2>
          </div>

          <Link
            href="/intake"
            className="inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 font-semibold !text-[#0f3f3f] shadow-lg transition-transform hover:-translate-y-0.5"
          >
            Start Registration Now
            <ArrowRight className="size-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-black/6 px-6 py-8 text-sm text-black/52 sm:px-10">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-medium">Aarohi by Aarogyam AI</p>
          <p>© {new Date().getFullYear()} Aarogyam AI. All rights reserved.</p>
        </div>
      </footer>
    </main>
  );
}

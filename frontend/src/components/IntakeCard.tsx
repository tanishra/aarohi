"use client";

import { useMemo } from "react";
import { ClipboardList } from "lucide-react";

import { useIntakeStore } from "@/store/useIntakeStore";

function prettifyKey(key: string): string {
  return key
    .replace(/[_-]+/g, " ")
    .replace(/([A-Z])/g, " $1")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export function IntakeCard() {
  const summary = useIntakeStore((state) => state.summary);

  const entries = useMemo(
    () =>
      Object.entries(summary).filter(
        ([, value]) => typeof value === "string" && value.trim().length > 0,
      ),
    [summary],
  );

  return (
    <section
      aria-label="Live intake"
      className="flex max-h-[42%] min-h-[120px] flex-col border-b border-black/6 bg-white/65 backdrop-blur-sm"
    >
      <header className="flex shrink-0 items-center gap-2 px-5 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-black/42">
        <ClipboardList className="size-4" />
        Live Intake
        <span className="ml-auto text-black/32">
          {entries.length} {entries.length === 1 ? "field" : "fields"}
        </span>
      </header>

      {entries.length === 0 ? (
        <p className="px-5 pb-4 text-sm italic text-black/40">
          Waiting for the conversation to begin...
        </p>
      ) : (
        <ul className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto px-5 pb-4">
          {entries.map(([key, value]) => (
            <li
              key={key}
              className="animate-intake-card rounded-xl border border-black/8 bg-white px-3 py-2 shadow-sm"
            >
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-black/38">
                {prettifyKey(key)}
              </p>
              <p className="mt-1 break-words text-sm font-medium text-black/80">
                {value}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

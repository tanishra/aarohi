import { clsx } from "clsx";
import { CheckCircle2, Circle } from "lucide-react";

interface ProgressBarProps {
  completedFields: string[];
}

const REQUIRED_STEPS = [
  { id: "Name", label: "Patient Name" },
  { id: "Age/Gender", label: "Age & Gender" },
  { id: "Contact", label: "Contact Info" },
  { id: "Symptoms", label: "Symptoms" },
  { id: "Duration/Severity", label: "Duration & Severity" },
  { id: "History", label: "Medical History" },
];

export function ProgressBar({ completedFields }: ProgressBarProps) {
  return (
    <div className="absolute left-6 top-6 z-30 hidden w-64 flex-col gap-2 rounded-[1.5rem] border border-black/8 bg-white/90 p-5 shadow-xl shadow-teal-900/5 backdrop-blur-md md:flex">
      <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-[var(--primary)]">
        Intake Progress
      </h3>
      <div className="flex flex-col gap-3">
        {REQUIRED_STEPS.map((step) => {
          const isCompleted = completedFields.includes(step.id);
          return (
            <div key={step.id} className="flex items-center gap-3">
              {isCompleted ? (
                <CheckCircle2 className="size-5 text-emerald-500" />
              ) : (
                <Circle className="size-5 text-black/20" />
              )}
              <span
                className={clsx(
                  "text-sm font-medium transition-colors",
                  isCompleted ? "text-black/80" : "text-black/40"
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

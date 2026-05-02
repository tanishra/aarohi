import { create } from "zustand";

interface IntakeState {
  summary: Record<string, string>;
  setSummary: (summary: Record<string, string>) => void;
  clearSummary: () => void;
}

export const useIntakeStore = create<IntakeState>((set) => ({
  summary: {},
  setSummary: (summary) => set({ summary }),
  clearSummary: () => set({ summary: {} }),
}));

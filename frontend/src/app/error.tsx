"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center min-h-full px-4">
      <h2 className="text-xl font-semibold text-[#191c1d] mb-2">
        Something went wrong
      </h2>
      <p className="text-[#5a6d72] text-center mb-6 max-w-md">
        {error.message || "An unexpected error occurred. Please try again."}
      </p>
      <button
        onClick={() => reset()}
        className="px-6 py-2 bg-[#6b8f71] text-white rounded-lg hover:bg-[#5a7b60] transition-colors"
      >
        Try again
      </button>
    </div>
  );
}

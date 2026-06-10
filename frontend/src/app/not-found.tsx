import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-full px-4">
      <h2 className="text-xl font-semibold text-[#191c1d] mb-2">
        Page not found
      </h2>
      <p className="text-[#5a6d72] text-center mb-6">
        The page you are looking for does not exist.
      </p>
      <Link
        href="/"
        className="px-6 py-2 bg-[#6b8f71] text-white rounded-lg hover:bg-[#5a7b60] transition-colors"
      >
        Go home
      </Link>
    </div>
  );
}

import type { Metadata } from "next";
import "@livekit/components-styles";

import "./globals.css";

export const metadata: Metadata = {
  title: "Aarohi – AI Patient Intake Assistant",
  description:
    "Experience the future of patient registration with Aarohi, an AI-powered nurse assistant by Aarogyam AI.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className="h-full antialiased light"
      style={{ colorScheme: "light" }}
    >
      <body
        className="min-h-full flex flex-col bg-[#f8fafa] text-[#191c1d]"
        style={{
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        }}
      >
        {children}
      </body>
    </html>
  );
}

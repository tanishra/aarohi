import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: false,
  turbopack: {},
  async rewrites() {
    return [
      {
        source: "/_next/static/chunks/:path*/avatar_core_wasm.js",
        destination: "/avatar_core_wasm.js",
      },
      {
        source: "/_next/static/chunks/avatar_core_wasm.js",
        destination: "/avatar_core_wasm.js",
      },
      {
        source: "/_next/static/chunks/:path*/avatar_core_wasm-e68766db.wasm",
        destination: "/avatar_core_wasm-e68766db.wasm",
      },
      {
        source: "/_next/static/chunks/avatar_core_wasm-e68766db.wasm",
        destination: "/avatar_core_wasm-e68766db.wasm",
      },
    ];
  },
  webpack(config) {
    const generator = config.module?.generator as
      | Record<string, unknown>
      | undefined;

    if (
      generator &&
      "asset" in generator &&
      generator.asset &&
      typeof generator.asset === "object" &&
      "filename" in (generator.asset as Record<string, unknown>)
    ) {
      if (!generator["asset/resource"]) {
        generator["asset/resource"] = generator.asset;
      }
      delete generator.asset;
    }

    return config;
  },
};

export default nextConfig;

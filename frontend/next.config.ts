import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "mintcdn.com",
      },
      {
        protocol: "https",
        hostname: "capsule-render.vercel.app",
      },
    ],
  },
  async headers() {
    return [
      {
        source: '/_avatarkit/:path*.wasm',
        headers: [{ key: 'Content-Type', value: 'application/wasm' }],
      },
    ];
  },
};

export default nextConfig;

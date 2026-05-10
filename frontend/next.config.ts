import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
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
};

export default nextConfig;

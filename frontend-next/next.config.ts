import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vercel injects its build adapter. Next 16.3 currently omits a root NFT
  // trace with that adapter, while standalone finalization still reads it.
  // Vercel does not use the standalone folder; keep it only for Docker builds.
  output: process.env.VERCEL ? undefined : "standalone",
};

export default nextConfig;

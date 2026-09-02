import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const internalApi = process.env.INTERNAL_API_BASE_URL ||
      (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : "");
    if (!internalApi) return [];
    return [{
      source: "/api",
      destination: `${internalApi}/api`,
    }];
  },
};

export default nextConfig;

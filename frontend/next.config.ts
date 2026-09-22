import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api-backend/:path*",
        destination: 'https://face-recognition-production-xxxx.up.railway.app/:path*',
      },
    ];
  },
};

export default nextConfig;

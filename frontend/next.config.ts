import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api-backend/:path*",
        destination: 'https://facerecognition-production-871d.up.railway.app/:path*',
      },
    ];
  },
};

export default nextConfig;

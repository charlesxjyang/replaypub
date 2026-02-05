import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async headers() {
    return [
      {
        source: '/dashboard',
        headers: [{ key: 'X-Robots-Tag', value: 'noindex' }],
      },
      {
        source: '/subscribe/:path*',
        headers: [{ key: 'X-Robots-Tag', value: 'noindex' }],
      },
      {
        source: '/unsubscribe',
        headers: [{ key: 'X-Robots-Tag', value: 'noindex' }],
      },
    ]
  },
};

export default nextConfig;

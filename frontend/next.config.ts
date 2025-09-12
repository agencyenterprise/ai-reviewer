import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'standalone',
  // Enable reliable hot reload when using the webpack dev server (non-Turbopack dev).
  // Ignored when running with Turbopack.
  webpack: (config, { dev }) => {
    if (dev) {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
};

export default nextConfig;

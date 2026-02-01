/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow API routes to handle Python backend
  async rewrites() {
    return [
      {
        source: '/api/agent/:path*',
        destination: 'http://localhost:8000/api/agent/:path*',
      },
    ];
  },
};

module.exports = nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // For Railway deployment
  // Allow API routes to handle Python backend
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/agent/:path*',
        destination: `${backendUrl}/api/agent/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

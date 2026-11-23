/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  transpilePackages: ["@driplytics/ui", "@driplytics/contracts"],
  poweredByHeader: false,
};

export default nextConfig;

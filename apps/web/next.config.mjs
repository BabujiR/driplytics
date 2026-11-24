/**
 * "standalone" output (a self-contained server folder for the production image, P0-23) copies
 * dependencies as symlinks. Windows only allows that with Developer Mode or as admin, so local
 * Windows builds skip it; Docker and CI (Linux) still build standalone.
 * Force it either way with NEXT_STANDALONE=1 / NEXT_STANDALONE=0.
 */
const standalone = process.env.NEXT_STANDALONE ? process.env.NEXT_STANDALONE === "1" : process.platform !== "win32";

/** @type {import('next').NextConfig} */
const nextConfig = {
  ...(standalone ? { output: "standalone" } : {}),
  reactStrictMode: true,
  transpilePackages: ["@driplytics/ui", "@driplytics/contracts"],
  poweredByHeader: false,
  // No floating "N" dev-tools button: it overlaps the sidebar and isn't part of the product UI.
  devIndicators: false,
};

export default nextConfig;

import type { NextConfig } from "next";

// Em produção o build é estático e servido pela ponte Python (dashboard/server.py),
// que também expõe /events e /api/*. No `next dev` essas rotas são encaminhadas a ela.
const apiOrigin = process.env.AGROMESH_API ?? "http://localhost:8080";
const isDev = process.env.NODE_ENV === "development";

const nextConfig: NextConfig = isDev
  ? {
      async rewrites() {
        return [
          { source: "/events", destination: `${apiOrigin}/events` },
          { source: "/api/:path*", destination: `${apiOrigin}/api/:path*` },
        ];
      },
    }
  : { output: "export", images: { unoptimized: true } };

export default nextConfig;

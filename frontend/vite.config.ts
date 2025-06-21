import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";
import { vitePlugin as remix } from "@remix-run/dev";

export default defineConfig({
  optimizeDeps: {
    include: ["@apollo/client", "@apollo/client/cache"],
  },
  ssr: {
    noExternal: ["@apollo/client"],
  },
  define: {
    'import.meta.env.VITE_BACKEND_API_URL': JSON.stringify(process.env.VITE_BACKEND_API_URL),
    'import.meta.env.VITE_WEBSOCKET_URL': JSON.stringify(process.env.VITE_WEBSOCKET_URL),
  },
  plugins: [
    remix({
      future: {
        v3_singleFetch: true,
        v3_fetcherPersist: true,
        v3_relativeSplatPath: true,
        v3_throwAbortReason: true,
        v3_lazyRouteDiscovery: true,
      },
    }),
    tsconfigPaths(),
  ],
});

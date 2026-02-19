import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import cesium from "vite-plugin-cesium";

const GITHUB_PAGES_BASE = "/Our-City-Health---Sentiment-Project/";

export default defineConfig(({ mode }) => {
  const base = mode === "production" ? GITHUB_PAGES_BASE : "/";

  return {
    base,
    plugins: [
      react(),
      // Pass the resolved base so vite-plugin-cesium sets CESIUM_BASE_URL
      // to the correct sub-path (critical for GitHub Pages).
      cesium({ rebuildCesium: false }),
    ],
    define: {
      // Ensure CESIUM_BASE_URL is always rooted at the Vite base path so
      // Cesium workers / imagery assets resolve correctly on GitHub Pages.
      "window.CESIUM_BASE_URL": JSON.stringify(`${base}cesium/`),
    },
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: "http://localhost:8001",
          changeOrigin: true,
        },
      },
    },
  };
});

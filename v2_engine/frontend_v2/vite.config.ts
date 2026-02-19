import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import cesium from "vite-plugin-cesium";

export default defineConfig(({ mode }) => {
  const isProd = mode === "production";

  return {
    // Relative base means asset URLs become "./assets/..." instead of
    // "/Our-City-Health---Sentiment-Project/assets/...". This is the most
    // reliable approach for GitHub Pages sub-directory deployments because
    // the URLs always resolve correctly relative to index.html.
    base: isProd ? "./" : "/",
    plugins: [
      react(),
      cesium(),
    ],
    // Override vite-plugin-cesium's hardcoded CESIUM_BASE_URL="/cesium/"
    // so Cesium workers load relative to the page (works on any sub-path).
    define: {
      CESIUM_BASE_URL: JSON.stringify(isProd ? "./cesium/" : "/cesium/"),
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

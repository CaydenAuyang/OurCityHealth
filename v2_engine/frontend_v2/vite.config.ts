import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import cesium from "vite-plugin-cesium";

const REPO = "Our-City-Health---Sentiment-Project";

export default defineConfig(({ mode }) => {
  const base = mode === "production" ? `/${REPO}/` : "/";

  return {
    base,
    plugins: [
      react(),
      // Default options — lets the plugin copy Cesium static assets to dist/cesium/
      cesium(),
    ],
    // Override vite-plugin-cesium's hardcoded CESIUM_BASE_URL="/cesium/" so
    // Cesium workers resolve under the GitHub Pages sub-path.
    define: {
      CESIUM_BASE_URL: JSON.stringify(`${base}cesium/`),
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

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import cesium from "vite-plugin-cesium";

export default defineConfig(({ mode }) => ({
  base:
    mode === "production"
      ? "/Our-City-Health---Sentiment-Project/"
      : "/",
  plugins: [
    react(),
    cesium(),
  ],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true,
      },
    },
  },
}));

import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        hud: {
          bg: "rgba(5, 10, 25, 0.82)",
          border: "rgba(0, 200, 255, 0.18)",
          accent: "#00d4ff",
          "accent-dim": "rgba(0, 212, 255, 0.35)",
          text: "#e2e8f0",
          muted: "#64748b",
          danger: "#fc8181",
          warning: "#f6e05e",
          success: "#68d391",
          panel: "rgba(8, 15, 35, 0.88)",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in": "fadeIn 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;

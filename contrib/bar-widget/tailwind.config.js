/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Sound Studio Theme
        background: {
          DEFAULT: "#0d0d0f",
          secondary: "#151518",
          elevated: "#1c1c21",
          hover: "#252529",
        },
        foreground: {
          DEFAULT: "#fafafa",
          secondary: "#a1a1aa",
          muted: "#71717a",
        },
        accent: {
          DEFAULT: "#f59e0b",
          glow: "#fbbf24",
          dim: "#b45309",
        },
        status: {
          success: "#22c55e",
          error: "#ef4444",
          warning: "#f59e0b",
        },
        border: {
          DEFAULT: "#27272a",
          focus: "#f59e0b",
        },
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "'SF Mono'", "'Cascadia Code'", "monospace"],
        display: ["'Space Grotesk'", "'DM Sans'", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "segment-flicker": "segment-flicker 0.1s ease-in-out",
        "led-on": "led-on 0.3s ease-out forwards",
      },
      keyframes: {
        "pulse-glow": {
          "0%, 100%": {
            opacity: "1",
            filter: "brightness(1) drop-shadow(0 0 4px var(--accent))",
          },
          "50%": {
            opacity: "0.7",
            filter: "brightness(1.2) drop-shadow(0 0 8px var(--accent))",
          },
        },
        "segment-flicker": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.8" },
        },
        "led-on": {
          "0%": {
            opacity: "0.3",
            filter: "brightness(0.5)",
          },
          "100%": {
            opacity: "1",
            filter: "brightness(1) drop-shadow(0 0 6px currentColor)",
          },
        },
      },
      boxShadow: {
        "led": "0 0 8px currentColor, inset 0 1px 1px rgba(255,255,255,0.1)",
        "panel": "inset 0 1px 0 rgba(255,255,255,0.05), inset 0 -1px 0 rgba(0,0,0,0.3)",
        "recess": "inset 0 2px 4px rgba(0,0,0,0.4), inset 0 1px 2px rgba(0,0,0,0.2)",
      },
    },
  },
  plugins: [],
}

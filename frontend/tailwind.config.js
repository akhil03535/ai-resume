/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#172554",
          50: "#EEF2FF",
          100: "#E0E7FF",
          600: "#2563EB",
          700: "#1D4ED8",
          900: "#172554",
        },
        accent: "#4F46E5",
        surface: "#FFFFFF",
        bg: "#F8FAFC",
        ink: {
          DEFAULT: "#0F172A",
          muted: "#475569",
        },
        border: "#E2E8F0",
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
        info: "#2563EB",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px 0 rgba(15, 23, 42, 0.04), 0 1px 3px 0 rgba(15, 23, 42, 0.06)",
      },
      borderRadius: {
        card: "10px",
      },
    },
  },
  plugins: [],
};

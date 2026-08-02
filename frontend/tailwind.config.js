/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Indigo primary — used for actions and focus.
        brand: {
          50: "#eef0fe",
          100: "#dfe2fd",
          200: "#c2c8fb",
          300: "#9aa3f7",
          400: "#6674ff",
          500: "#4c5bf5",
          600: "#3b45db",
          700: "#2f37b0",
          800: "#282e8c",
          900: "#242a70",
        },
        // Near-black slate — dark surfaces.
        night: {
          950: "#0a0c10",
          900: "#0c0e12",
          800: "#14171d",
          700: "#1b1f27",
          600: "#262b34",
          500: "#333a45",
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', "ui-sans-serif", "system-ui", "sans-serif"],
        sans: ['"Inter"', "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(16,18,24,0.04), 0 8px 24px -12px rgba(16,18,24,0.12)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.4s ease-out both",
      },
    },
  },
  plugins: [],
};

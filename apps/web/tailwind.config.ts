import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17201a",
        mint: "#0f7b63",
        saffron: "#d9911b",
        paper: "#f7f8f4"
      }
    }
  },
  plugins: []
};

export default config;

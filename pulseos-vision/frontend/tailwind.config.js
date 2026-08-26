/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'pulse-dark': '#0a0a0a',
        'pulse-accent': '#00ffcc',
        'pulse-glass': 'rgba(255, 255, 255, 0.05)',
      }
    },
  },
  plugins: [],
}

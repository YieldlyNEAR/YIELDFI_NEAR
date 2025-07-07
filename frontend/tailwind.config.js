/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      colors: {
        'near-green': '#00ec97',
        'near-blue': '#17d9d4',
        'near-purple': '#9797ff',
        'near-red': '#ff7966',
        'near-bg': '#f2f1e9',
      },
    },
  },
  plugins: [],
}
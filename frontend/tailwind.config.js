/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0F1318',
        surface: '#171C23',
        primary: '#D4D8DD',
        muted: '#3A4A5A',
        gold: '#BFA046',
        silver: '#C8CDD3',
        correct: '#5A8A6A',
        wrong: '#7A3A3A',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

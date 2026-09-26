/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fff8f1',
          100: '#feeee2',
          200: '#fcdcc5',
          300: '#f9c19d',
          400: '#f59a68',
          500: '#f1763a',
          600: '#e25923',
          700: '#bb421a',
          800: '#95361b',
          900: '#792f1a',
          950: '#41150a',
        },
        dark: {
          800: '#161b22',
          850: '#11151c',
          900: '#0d1117',
          950: '#080a0e',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}

import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#6C47FF',
          deep: '#4D2DB7',
          dark: '#361999',
          light: '#A388FF',
          bg: '#0E0E12',
          surface: '#18181F',
          border: '#2B2B36',
          white: '#FFFFFF',
          muted: '#9CA3AF'
        }
      }
    },
  },
  plugins: [],
} satisfies Config

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': {
          primary: '#0a0a0a',
          secondary: '#111111',
          tertiary: '#1a1a1a',
          card: '#151515',
          hover: '#1f1f1f',
        },
        'dark-border': {
          primary: '#262626',
          secondary: '#2a2a2a',
        },
        'dark-text': {
          primary: '#f5f5f5',
          secondary: '#a3a3a3',
          tertiary: '#737373',
        },
      },
    },
  },
  plugins: [],
}


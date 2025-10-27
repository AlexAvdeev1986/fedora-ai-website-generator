/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fedora: {
          blue: '#3b6ea5',
          purple: '#77216F',
          light: '#f8f9fa',
          dark: '#2c2c2c'
        }
      },
      fontFamily: {
        'fedora': ['Cantarell', 'Ubuntu', 'sans-serif']
      },
      animation: {
        'pulse-slow': 'pulse 3s linear infinite',
        'bounce-slow': 'bounce 2s infinite'
      }
    },
  },
  plugins: [],
}
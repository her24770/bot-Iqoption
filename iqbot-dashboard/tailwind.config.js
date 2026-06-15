/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: '#0b0f17',
        panel: '#141a26',
        accent: '#3b82f6',
      },
    },
  },
  plugins: [],
}

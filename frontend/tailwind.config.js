/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        control: {
          bg: '#0a1128',
          card: '#101a36',
          surface: '#152248',
          border: '#1e2d5a',
          borderHover: '#00bbf9',
        },
        neon: {
          cyan: '#00bbf9',
          green: '#00f5d4',
          amber: '#ffd166',
          rose: '#ff3864',
        },
      },
    },
  },
  plugins: [],
};

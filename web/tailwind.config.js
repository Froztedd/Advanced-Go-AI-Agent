/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        wood: {
          50:  '#fbf6ec',
          100: '#f5ead2',
          200: '#ead4a4',
          300: '#dcb872',
          400: '#c69b4d',
          500: '#a87a35',
          600: '#85602a',
          700: '#634621',
          800: '#3f2d16',
          900: '#23190d',
        },
        ink: {
          900: '#0d0f12',
          800: '#15181d',
          700: '#1d2129',
          600: '#2a2f39',
          500: '#3a414e',
          400: '#5b6373',
          300: '#8e96a4',
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', 'ui-serif', 'Georgia', 'serif'],
        body: ['"Inter"', 'ui-sans-serif', 'system-ui'],
      },
      boxShadow: {
        stone: '0 2px 4px rgba(0,0,0,0.5), inset -2px -2px 4px rgba(0,0,0,0.4), inset 2px 2px 3px rgba(255,255,255,0.15)',
        stoneLight: '0 2px 4px rgba(0,0,0,0.4), inset -2px -2px 4px rgba(0,0,0,0.15), inset 2px 2px 3px rgba(255,255,255,0.7)',
        board: '0 30px 80px -20px rgba(0,0,0,0.6), 0 10px 20px -5px rgba(0,0,0,0.3)',
      },
      keyframes: {
        'fade-in-up': {
          '0%':   { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: '0.6' },
          '50%':      { opacity: '1' },
        },
      },
      animation: {
        'fade-in-up': 'fade-in-up 0.6s ease-out both',
        'pulse-soft': 'pulse-soft 1.6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}

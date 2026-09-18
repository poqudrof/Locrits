/** @type {import('tailwindcss').Config} */
// Même structure que la landing de Plati : seule la couleur primaire change
// (indigo pour Locrits), l'ambre secondaire est partagé entre les deux produits.
module.exports = {
  content: ['./index.html'],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: '#4338CA', dark: '#3730A3', light: '#6366F1' },
        secondary: { DEFAULT: '#D97706', dark: '#b86205' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  // Ajoutées par le JS (menu mobile), donc absentes d'une partie du markup.
  safelist: ['hidden', 'flex'],
}

import type { Config } from 'tailwindcss'
import defaultTheme from 'tailwindcss/defaultTheme'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        'dm-mono': ['DM Mono', ...defaultTheme.fontFamily.mono],
        'libre-baskerville': ['Libre Baskerville', ...defaultTheme.fontFamily.serif],
        'tiro-bangla': ['Tiro Bangla', ...defaultTheme.fontFamily.sans],
      },
      colors: {
        void: 'var(--bg-void)',
        surface: 'var(--bg-surface)',
        raised: 'var(--bg-raised)',
        subtle: 'var(--bg-subtle)',
        paper: 'var(--bg-paper)',
        'border-dim': 'var(--border-dim)',
        'border-warm': 'var(--border-warm)',
        'border-gold': 'var(--border-gold)',
        gold: 'var(--gold)',
        'gold-bright': 'var(--gold-bright)',
        'ink-red': 'var(--ink-red)',
        'ink-green': 'var(--ink-green)',
        'ink-teal': 'var(--ink-teal)',
        'ink-teal-bright': 'var(--ink-teal-bright)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',
        'text-on-gold': 'var(--text-on-gold)',
      },
      backgroundImage: {
        'paper-glow': 'var(--paper-glow)',
        grain: 'var(--grain)',
      },
      boxShadow: {
        lamp: 'var(--lamp-shadow)',
      },
    },
  },
  plugins: [],
} satisfies Config

import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify, type ThemeDefinition } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const lightTheme: ThemeDefinition = {
  dark: false,
  colors: {
    primary: '#667eea',
    secondary: '#764ba2',
    accent: '#8b5cf6',
    error: '#ef4444',
    warning: '#f59e0b',
    info: '#3b82f6',
    success: '#10b981',
    background: '#f8fafc',
    surface: '#ffffff'
  }
}

const darkTheme: ThemeDefinition = {
  dark: true,
  colors: {
    primary: '#818cf8',
    secondary: '#a78bfa',
    accent: '#c4b5fd',
    error: '#f87171',
    warning: '#fbbf24',
    info: '#60a5fa',
    success: '#34d399',
    background: '#0f172a',
    surface: '#1e293b'
  }
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'light',
    themes: {
      light: lightTheme,
      dark: darkTheme
    }
  },
  defaults: {
    VCard: {
      elevation: 2
    },
    VBtn: {
      rounded: 'lg'
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable'
    },
    VTextarea: {
      variant: 'outlined',
      density: 'comfortable'
    }
  }
})

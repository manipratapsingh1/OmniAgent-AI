/**
 * Design System & Theme Configuration
 * Centralized theme tokens for consistent, professional design
 */

export const THEME = {
  // Color Palette
  colors: {
    // Primary brand colors
    primary: {
      50: "#f3f0ff",
      100: "#ede9fe",
      200: "#ddd6fe",
      300: "#c4b5fd",
      400: "#a78bfa",
      500: "#8b5cf6",
      600: "#7c3aed",
      700: "#6d28d9",
      800: "#5b21b6",
      900: "#4c1d95",
    },
    // Secondary blue
    secondary: {
      50: "#f0f9ff",
      100: "#e0f2fe",
      200: "#bae6fd",
      300: "#7dd3fc",
      400: "#38bdf8",
      500: "#0ea5e9",
      600: "#0284c7",
      700: "#0369a1",
      800: "#075985",
      900: "#0c4a6e",
    },
    // Neutral grays
    neutral: {
      50: "#f9fafb",
      100: "#f3f4f6",
      200: "#e5e7eb",
      300: "#d1d5db",
      400: "#9ca3af",
      500: "#6b7280",
      600: "#4b5563",
      700: "#374151",
      800: "#1f2937",
      900: "#111827",
    },
    // Status colors
    status: {
      success: { light: "#dcfce7", main: "#22c55e", dark: "#15803d" },
      error: { light: "#fee2e2", main: "#ef4444", dark: "#7f1d1d" },
      warning: { light: "#fef3c7", main: "#f59e0b", dark: "#92400e" },
      info: { light: "#dbeafe", main: "#3b82f6", dark: "#1e40af" },
    },
    // Surface colors (for glass effect panels)
    surface: {
      dark: "rgba(15, 23, 42, 0.8)",
      darkMedium: "rgba(30, 41, 59, 0.6)",
      darkLight: "rgba(51, 65, 85, 0.4)",
    },
  },

  // Typography System
  typography: {
    fontFamily: {
      base: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      mono: '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, "Courier New", monospace',
    },
    fontSize: {
      xs: { size: "0.75rem", lineHeight: "1rem" },       // 12px
      sm: { size: "0.875rem", lineHeight: "1.25rem" },   // 14px
      base: { size: "1rem", lineHeight: "1.5rem" },      // 16px
      lg: { size: "1.125rem", lineHeight: "1.75rem" },   // 18px
      xl: { size: "1.25rem", lineHeight: "1.75rem" },    // 20px
      "2xl": { size: "1.5rem", lineHeight: "2rem" },     // 24px
      "3xl": { size: "1.875rem", lineHeight: "2.25rem" }, // 30px
      "4xl": { size: "2.25rem", lineHeight: "2.5rem" },  // 36px
    },
    fontWeight: {
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
    },
  },

  // Spacing System (8px base unit)
  spacing: {
    0: "0",
    1: "0.25rem",    // 4px
    2: "0.5rem",     // 8px
    3: "0.75rem",    // 12px
    4: "1rem",       // 16px
    6: "1.5rem",     // 24px
    8: "2rem",       // 32px
    12: "3rem",      // 48px
    16: "4rem",      // 64px
    20: "5rem",      // 80px
    24: "6rem",      // 96px
  },

  // Shadows & Elevation System
  shadows: {
    none: "none",
    xs: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    sm: "0 1px 2px 0 rgba(0, 0, 0, 0.1)",
    md: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    lg: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
    "2xl": "0 25px 50px -12px rgba(0, 0, 0, 0.25)",
    // Glow effects
    glow: {
      sm: "0 0 12px rgba(59, 130, 246, 0.3)",
      md: "0 0 24px rgba(139, 92, 246, 0.4)",
      lg: "0 0 36px rgba(139, 92, 246, 0.5)",
    },
  },

  // Border Radius System
  borderRadius: {
    none: "0",
    sm: "0.375rem",   // 6px
    md: "0.5rem",     // 8px
    lg: "0.75rem",    // 12px
    xl: "1rem",       // 16px
    "2xl": "1.5rem",  // 24px
    full: "9999px",
  },

  // Animation & Transition Timings
  animation: {
    duration: {
      fast: 150,      // ms
      base: 300,
      slow: 500,
      slower: 750,
    },
    easing: {
      linear: "linear",
      in: "cubic-bezier(0.4, 0, 1, 1)",
      out: "cubic-bezier(0, 0, 0.2, 1)",
      inOut: "cubic-bezier(0.4, 0, 0.2, 1)",
    },
  },

  // Component Sizes
  componentSizes: {
    // Button sizes
    button: {
      xs: { padding: "0.375rem 0.75rem", fontSize: "0.75rem" },
      sm: { padding: "0.5rem 1rem", fontSize: "0.875rem" },
      md: { padding: "0.625rem 1.25rem", fontSize: "1rem" },
      lg: { padding: "0.75rem 1.5rem", fontSize: "1.125rem" },
      xl: { padding: "1rem 2rem", fontSize: "1.25rem" },
    },
    // Input sizes
    input: {
      sm: { padding: "0.5rem 0.75rem", fontSize: "0.875rem" },
      md: { padding: "0.625rem 1rem", fontSize: "1rem" },
      lg: { padding: "0.75rem 1.25rem", fontSize: "1.125rem" },
    },
  },

  // Z-index scale
  zIndex: {
    hide: -1,
    base: 0,
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    backdrop: 1040,
    offcanvas: 1050,
    modal: 1060,
    popover: 1070,
    tooltip: 1080,
  },

  // Breakpoints for responsive design
  breakpoints: {
    xs: "320px",
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },
} as const;

// Helper function to get contrasting text color
export const getTextColor = (backgroundColor: string): string => {
  // Simple luminance-based approach
  return backgroundColor.toLowerCase().includes("dark") ? "#ffffff" : "#111827";
};

// Export individual theme parts for easier importing
export const { colors, typography, spacing, shadows, animation } = THEME;

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: { "/api": "http://localhost:8000" },
  },
  build: {
    outDir: "dist",
    sourcemap: false,  // Disable sourcemaps in production for smaller build
    minify: "terser",  // Use Terser for better minification
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.log in production
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom", "react-router-dom", "zustand", "axios"],
          ui: ["framer-motion", "react-icons"],
          markdown: ["react-markdown", "remark-gfm"],
        },
      },
    },
    chunkSizeWarningLimit: 500,  // Warn if chunks are > 500KB
  },
});
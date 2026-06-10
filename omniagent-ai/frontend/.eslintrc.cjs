module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: "module",
    ecmaFeatures: { jsx: true },
  },
  settings: {
    react: { version: "detect" },
  },
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:jsx-a11y/recommended",
    "prettier"
  ],
  plugins: ["react", "react-hooks", "@typescript-eslint", "jsx-a11y"],
  rules: {
    "react/react-in-jsx-scope": "off",
    "@typescript-eslint/no-unused-vars": ["warn", { "argsIgnorePattern": "^_" }],
    // Relax some rules to allow staged fixes across the codebase
    "@typescript-eslint/no-explicit-any": "warn",
    "jsx-a11y/label-has-associated-control": "warn",
    "react/no-unescaped-entities": "warn",
    "no-constant-condition": "warn",
    "jsx-a11y/anchor-is-valid": "off",
    "react/prop-types": "off"
  },
  ignorePatterns: ["dist/", "node_modules/", "tsconfig.tsbuildinfo", "**/*.js", "**/*.jsx"]
}

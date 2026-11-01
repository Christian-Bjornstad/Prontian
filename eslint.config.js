import js from "@eslint/js";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    files: ["pronto_report/static/*.js"],
    languageOptions: { globals: globals.browser },
  },
  {
    files: ["scripts/*.mjs", "eslint.config.js"],
    languageOptions: { globals: globals.node },
  },
];

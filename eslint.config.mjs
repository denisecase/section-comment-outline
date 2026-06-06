// ============================================================
// eslint.config.mjs
// ============================================================
// Updated: 2026-06-06
//
// REQ: TypeScript extension projects SHOULD use ESLint for source quality.
// WHY: Catch TypeScript, JavaScript, and extension-source issues before CI/release.
// OBS: TypeScript compiler settings remain in tsconfig.json.
// CUSTOM: Add extension-specific rules only when they improve maintainability.

import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  // === Global ignores ===

  {
    ignores: [
      ".vscode-test/**",
      "coverage/**",
      "dist/**",
      "node_modules/**",
      "out/**",
    ],
  },

  // === JavaScript baseline ===

  js.configs.recommended,

  // === TypeScript baseline ===

  ...tseslint.configs.recommendedTypeChecked,

  // === TypeScript project rules ===

  {
    files: ["src/**/*.ts", "test/**/*.ts"],
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.test.json",
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // WHY: Explicit boundaries make extension behavior easier to review.
      "@typescript-eslint/explicit-function-return-type": [
        "warn",
        {
          allowExpressions: true,
        },
      ],

      // WHY: Prefer const for stable local values and smaller diffs.
      "prefer-const": "error",

      // WHY: Extension APIs often require async behavior; floating promises hide failures.
      "@typescript-eslint/no-floating-promises": "error",

      // WHY: Avoid accidentally accepting unchecked values from extension APIs.
      "@typescript-eslint/no-unsafe-assignment": "warn",
      "@typescript-eslint/no-unsafe-member-access": "warn",

      // WHY: Keep imports one-directional; source should not import compiled output.
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["../out/**", "../../out/**", "out/**"],
              message: "Do not import compiled output from source or tests.",
            },
          ],
        },
      ],
    },
  },

  // === Test-specific rules ===

  {
    files: ["test/**/*.ts"],
    rules: {
      // WHY: Tests may use flexible assertions and fixtures.
      "@typescript-eslint/no-unsafe-assignment": "off",
      "@typescript-eslint/no-unsafe-member-access": "off",
    },
  },
);

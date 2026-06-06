// ============================================================
// src/config.ts
// ============================================================
// Updated: 2026-06-06
//
// REQ: Extension configuration SHOULD be read through a small typed boundary.
// WHY: Keep VS Code settings access isolated from parsing and symbol-provider logic.
// OBS: Defaults support common structured comment section styles.
// CUSTOM: Add settings only when they change user-visible extension behavior.

import * as vscode from "vscode";

// === Configuration constants ===

export const CONFIG_SECTION = "commentSectionOutline";

export const DEFAULT_SECTION_PATTERNS = [
  "^\\s*#\\s*===\\s*(.*?)\\s*===\\s*$",
  "^\\s*//\\s*===\\s*(.*?)\\s*===\\s*$",
  "^\\s*<!--\\s*===\\s*(.*?)\\s*===\\s*-->\\s*$",
  "^\\s*/\\*\\s*===\\s*(.*?)\\s*===\\s*\\*/\\s*$",
] as const;

// === Public configuration model ===

export interface ExtensionConfig {
  enabled: boolean;
  includeDefaultPatterns: boolean;
  patterns: readonly string[];
}

// === Configuration loading ===

export function getExtensionConfig(): ExtensionConfig {
  const config = vscode.workspace.getConfiguration(CONFIG_SECTION);

  const enabled = config.get<boolean>("enabled", true);
  const includeDefaultPatterns = config.get<boolean>(
    "includeDefaultPatterns",
    true,
  );
  const customPatterns = config.get<string[]>("patterns", []);

  const patterns = includeDefaultPatterns
    ? [...DEFAULT_SECTION_PATTERNS, ...customPatterns]
    : customPatterns;

  return {
    enabled,
    includeDefaultPatterns,
    patterns,
  };
}

// === Pattern compilation ===

export function compilePatterns(patterns: readonly string[]): RegExp[] {
  return patterns
    .map((pattern) => compilePattern(pattern))
    .filter((pattern): pattern is RegExp => pattern !== undefined);
}

function compilePattern(pattern: string): RegExp | undefined {
  try {
    return new RegExp(pattern);
  } catch {
    // Invalid user-provided patterns are ignored so one bad setting does not
    // break the extension for the whole workspace.
    return undefined;
  }
}

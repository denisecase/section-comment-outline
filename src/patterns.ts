// ============================================================
// src/patterns.ts
// ============================================================
// Updated: 2026-06-06
//
// REQ: Section parsing SHOULD recognize structured comment section headers.
// WHY: Keep regex matching separate from VS Code document-symbol behavior.
// CUSTOM: Add supported comment styles only when they are part of the extension contract.

import { DEFAULT_SECTION_PATTERNS, compilePatterns } from "./config";

// === Section extraction ===

export function getSectionName(line: string): string | undefined {
  const patterns = compilePatterns(DEFAULT_SECTION_PATTERNS);

  for (const pattern of patterns) {
    const match = line.match(pattern);
    const sectionName = match?.[1]?.trim();

    if (isValidSectionName(sectionName)) {
      return sectionName;
    }
  }

  return undefined;
}

// === Section validation ===

function isValidSectionName(
  sectionName: string | undefined,
): sectionName is string {
  if (!sectionName) {
    return false;
  }

  return /[A-Za-z0-9]/.test(sectionName);
}

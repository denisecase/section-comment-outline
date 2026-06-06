// ============================================================
// test/suite/patterns.test.ts
// ============================================================
// Updated: 2026-06-06
//
// REQ: Section parsing behavior SHOULD be tested independently from VS Code APIs.
// WHY: Regex behavior is the core extension contract and should be easy to verify.
// CUSTOM: Add cases when new supported comment styles are introduced.

import * as assert from "assert";

import { DEFAULT_SECTION_PATTERNS, compilePatterns } from "../../src/config";

// === Test helpers ===

function findSectionName(line: string): string | undefined {
  const patterns = compilePatterns(DEFAULT_SECTION_PATTERNS);

  for (const pattern of patterns) {
    const match = line.match(pattern);
    const sectionName = match?.[1]?.trim();

    if (sectionName) {
      return sectionName;
    }
  }

  return undefined;
}

// === Pattern tests ===

suite("Section comment patterns", () => {
  test("matches hash comment section headers", () => {
    assert.strictEqual(
      findSectionName("# === Core defaults ==="),
      "Core defaults",
    );
  });

  test("matches slash comment section headers", () => {
    assert.strictEqual(
      findSectionName("// === TypeScript project rules ==="),
      "TypeScript project rules",
    );
  });

  test("matches Markdown HTML comment section headers", () => {
    assert.strictEqual(
      findSectionName("<!-- === Configuration === -->"),
      "Configuration",
    );
  });

  test("matches block comment section headers", () => {
    assert.strictEqual(
      findSectionName("/* === Extension source === */"),
      "Extension source",
    );
  });

  test("trims section names", () => {
    assert.strictEqual(
      findSectionName("# ===   Named root and metadata files   ==="),
      "Named root and metadata files",
    );
  });

  test("does not match ordinary hash comments", () => {
    assert.strictEqual(
      findSectionName("# This ordinary comment should not appear in Outline."),
      undefined,
    );
  });

  test("does not match ordinary Markdown comments", () => {
    assert.strictEqual(
      findSectionName("<!-- This ordinary comment should not appear. -->"),
      undefined,
    );
  });

  test("ignores invalid custom regex patterns", () => {
    const patterns = compilePatterns([
      "^\\s*#\\s*===\\s*(.*?)\\s*===\\s*$",
      "[",
    ]);

    assert.strictEqual(patterns.length, 1);

    const firstPattern = patterns[0];
    assert.ok(firstPattern);

    assert.strictEqual(
      "# === Valid section ===".match(firstPattern)?.[1],
      "Valid section",
    );
  });
});

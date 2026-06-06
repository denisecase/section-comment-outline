// ============================================================
// test/runTest.ts
// ============================================================
// Updated: 2026-06-06
//
// REQ: VS Code extension projects SHOULD run integration tests through VS Code.
// WHY: @vscode/test-electron launches an Extension Development Host and runs
// the compiled Mocha test suite in a realistic VS Code environment.
// CUSTOM: Update extensionDevelopmentPath or extensionTestsPath only if the
// compiled output layout changes.

import * as path from "path";

import { runTests } from "@vscode/test-electron";

// === Test runner ===

async function main(): Promise<void> {
  try {
    const extensionDevelopmentPath = path.resolve(__dirname, "../..");
    const extensionTestsPath = path.resolve(__dirname, "./suite/index");

    await runTests({
      extensionDevelopmentPath,
      extensionTestsPath,
    });
  } catch (error) {
    console.error("Failed to run extension tests.");
    console.error(error);
    process.exit(1);
  }
}

void main();

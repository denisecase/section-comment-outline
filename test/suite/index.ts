// ============================================================
// test/suite/index.ts
// ============================================================
// Updated: 2026-06-06
//
// REQ: VS Code extension tests SHOULD provide one compiled suite entrypoint.
// CUSTOM: Update the file pattern only if the compiled test layout changes.

import { runExtensionTests } from "./extension.test";
import { runPatternTests } from "./patterns.test";

export async function run(): Promise<void> {
  await runPatternTests();
  await runExtensionTests();
}

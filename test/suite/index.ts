// ============================================================
// test/suite/index.ts
// ============================================================
// Updated: 2026-06-06
//
// REQ: VS Code extension tests SHOULD provide one compiled suite entrypoint.
// WHY: @vscode/test-electron loads one test module, which then discovers and
// runs the compiled Mocha test files.
// CUSTOM: Update the file pattern only if the compiled test layout changes.

import * as fs from "fs";
import * as path from "path";

import Mocha from "mocha";

// === Test helpers ===

function asError(error: unknown): Error {
  if (error instanceof Error) {
    return error;
  }

  return new Error(String(error));
}

// === Test suite runner ===

export function run(): Promise<void> {
  const mocha = new Mocha({
    color: true,
    ui: "tdd",
  });

  const testsRoot = __dirname;

  return new Promise((resolve, reject) => {
    fs.readdir(testsRoot, (error, files) => {
      if (error) {
        reject(
          new Error(`Failed to read test suite directory: ${error.message}`),
        );
        return;
      }

      for (const file of files) {
        if (file.endsWith(".test.js")) {
          mocha.addFile(path.resolve(testsRoot, file));
        }
      }

      try {
        mocha.run((failures) => {
          if (failures > 0) {
            reject(new Error(`${failures} tests failed.`));
          } else {
            resolve();
          }
        });
      } catch (runError) {
        reject(asError(runError));
      }
    });
  });
}

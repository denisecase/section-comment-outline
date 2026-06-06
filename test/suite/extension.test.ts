// ============================================================
// test/suite/extension.test.ts
// ============================================================
// Updated: 2026-06-06
//
// REQ: Extension behavior SHOULD be tested against representative repo files.
// WHY: Fixtures verify Outline symbols for .gitattributes, Markdown,
// PowerShell, TOML, and YAML-style files.
// CUSTOM: Add fixtures when new comment styles or file families are supported.

import * as assert from "assert";
import * as path from "path";
import * as vscode from "vscode";

import { SectionSymbolProvider } from "../../src/sectionSymbolProvider";

// === Test helpers ===

const fixtureRoot = path.resolve(__dirname, "../../../test/fixtures");

async function openFixture(filename: string): Promise<vscode.TextDocument> {
  const uri = vscode.Uri.file(path.join(fixtureRoot, filename));
  return vscode.workspace.openTextDocument(uri);
}

async function getSymbolNames(filename: string): Promise<string[]> {
  const document = await openFixture(filename);
  const provider = new SectionSymbolProvider();

  const symbols = await provider.provideDocumentSymbols(
    document,
    new vscode.CancellationTokenSource().token,
  );

  return (symbols ?? []).map((symbol) => symbol.name);
}

function assertSymbolNames(actual: string[], expected: string[]): void {
  assert.deepStrictEqual(actual, expected);
}

// === Extension tests ===

suite("Comment Section Outline extension", () => {
  test("extracts sections from gitattributes fixture", async () => {
    const names = await getSymbolNames("gitattributes.txt");

    assertSymbolNames(names, [
      "Core defaults",
      "Named root and metadata files",
      "Programming languages and scripts",
      "Logs and generated runtime output",
    ]);
  });

  test("extracts sections from Markdown fixture", async () => {
    const names = await getSymbolNames("markdown.md");

    assertSymbolNames(names, ["Overview", "Usage", "Configuration"]);
  });

  test("extracts sections from PowerShell fixture", async () => {
    const names = await getSymbolNames("powershell.ps1");

    assertSymbolNames(names, ["Setup", "Validate", "Complete"]);
  });

  test("extracts sections from TOML fixture", async () => {
    const names = await getSymbolNames("toml.txt");

    assertSymbolNames(names, [
      "Repository identity",
      "Declared repository surfaces",
      "Required self-protection",
    ]);
  });

  test("extracts sections from YAML fixture", async () => {
    const names = await getSymbolNames("yaml.txt");

    assertSymbolNames(names, ["Workflow triggers", "Permissions", "Jobs"]);
  });
});

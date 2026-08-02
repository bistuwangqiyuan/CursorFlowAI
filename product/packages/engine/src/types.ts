export type Severity = "critical" | "warn" | "info";

export type TriangleLeg = "agent" | "untrusted_input" | "high_privilege" | "exfiltration";

export interface SourceRef {
  /** Stable ID used in research/sources.md and docs */
  id: string;
  title: string;
  url: string;
}

export interface Finding {
  ruleId: string;
  severity: Severity;
  title: string;
  message: string;
  legs: TriangleLeg[];
  file?: string;
  line?: number;
  remediation: string;
  sources: SourceRef[];
}

export interface ScanOptions {
  /** Display name for the scanned document */
  filename?: string;
}

export interface ScanResult {
  filename: string;
  findings: Finding[];
  summary: {
    critical: number;
    warn: number;
    info: number;
    legsPresent: TriangleLeg[];
    fatalTriangle: boolean;
  };
  /** Engine never claims compliance */
  disclaimer: string;
}

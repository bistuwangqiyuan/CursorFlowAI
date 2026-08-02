/** Strip `# ...` comments so keyword search does not hit fixture prose. */
export function stripYamlComments(source: string): string {
  return source
    .split(/\r?\n/)
    .map((line) => {
      const inSingle = false;
      void inSingle;
      const hash = line.indexOf("#");
      if (hash === -1) return line;
      // Keep full-line comments as blanks to preserve line numbers
      if (line.slice(0, hash).trim() === "") return "";
      return line.slice(0, hash);
    })
    .join("\n");
}

/** 1-based line of first regex match in source, or undefined. */
export function findLine(source: string, pattern: RegExp): number | undefined {
  const searchable = stripYamlComments(source);
  const flags = pattern.flags.includes("m")
    ? pattern.flags.includes("g")
      ? pattern.flags
      : `${pattern.flags}g`
    : pattern.flags.includes("g")
      ? `${pattern.flags}m`
      : `${pattern.flags}gm`;
  const re = new RegExp(pattern.source, flags);
  const match = re.exec(searchable);
  if (!match || match.index === undefined) return undefined;
  return searchable.slice(0, match.index).split(/\r?\n/).length;
}

export function normalizeTriggers(on: unknown): string[] {
  if (on == null) return [];
  if (typeof on === "string") return [on];
  if (Array.isArray(on)) return on.map(String);
  if (typeof on === "object") return Object.keys(on as object);
  return [];
}

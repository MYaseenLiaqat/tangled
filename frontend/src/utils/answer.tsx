import { ReactNode } from "react";

/**
 * Render a tutor answer: a small, safe subset of Markdown (paragraphs, bullet/numbered lists,
 * headings, **bold**, *italic*, `code`) plus [n] citations. Builds React elements only, never HTML
 * strings, so model output cannot inject markup. Citations that don't match a known source are dropped.
 */
const INLINE = /(\*\*[^*\n]+\*\*|__[^_\n]+__|`[^`\n]+`|\[\d+(?:\s*,\s*\d+)*\]|\*[^*\s][^*\n]*\*|_[^_\s][^_\n]*_)/g;

function inline(text: string, sources: Set<number>, keyPrefix: string): ReactNode[] {
  return text.split(INLINE).map((part, index): ReactNode => {
    const key = `${keyPrefix}-${index}`;
    if (!part) return null;
    // [1] or grouped [1, 2]: one superscript per known source, unknown numbers dropped.
    if (/^\[\d+(?:\s*,\s*\d+)*\]$/.test(part)) {
      const known = part.slice(1, -1).split(",").map(n => Number(n.trim())).filter(n => sources.has(n));
      return known.length ? <span className="cites" key={key}>{known.map(n => <sup key={`${key}-${n}`}>[{n}]</sup>)}</span> : null;
    }
    if (/^(\*\*|__).+(\*\*|__)$/.test(part)) return <strong key={key}>{inline(part.slice(2, -2), sources, key)}</strong>;
    if (/^`.+`$/.test(part)) return <code key={key}>{part.slice(1, -1)}</code>;
    if (/^[*_].+[*_]$/.test(part)) return <em key={key}>{inline(part.slice(1, -1), sources, key)}</em>;
    return part;
  });
}

type Block = { kind: "p" | "ul" | "ol" | "h"; lines: string[] };

function blocks(answer: string): Block[] {
  const out: Block[] = [];
  let current: Block | null = null;
  for (const raw of answer.replace(/\r\n/g, "\n").split("\n")) {
    const line = raw.trim();
    if (!line) { current = null; continue; }
    const bullet = line.match(/^[-*•]\s+(.*)$/);
    const numbered = line.match(/^\d+[.)]\s+(.*)$/);
    const heading = line.match(/^#{1,6}\s+(.*)$/);
    const [kind, text]: [Block["kind"], string] = bullet ? ["ul", bullet[1]] : numbered ? ["ol", numbered[1]]
      : heading ? ["h", heading[1]] : ["p", line];
    if (kind === "h" || !current || current.kind !== kind) {
      current = { kind, lines: [text] };
      out.push(current);
      if (kind === "h") current = null;
    } else {
      current.lines.push(text);
    }
  }
  return out;
}

export function renderAnswer(answer: string, sourceNumbers: number[]): ReactNode {
  const sources = new Set(sourceNumbers);
  return <div className="answer">{blocks(answer).map((block, i) => {
    const key = `b${i}`;
    if (block.kind === "ul" || block.kind === "ol") {
      const items = block.lines.map((line, j) => <li key={`${key}-${j}`}>{inline(line, sources, `${key}-${j}`)}</li>);
      return block.kind === "ul" ? <ul key={key}>{items}</ul> : <ol key={key}>{items}</ol>;
    }
    if (block.kind === "h") return <p key={key}><strong>{inline(block.lines[0], sources, key)}</strong></p>;
    return <p key={key}>{block.lines.map((line, j) => <span key={`${key}-${j}`}>{j > 0 && <br />}{inline(line, sources, `${key}-${j}`)}</span>)}</p>;
  })}</div>;
}

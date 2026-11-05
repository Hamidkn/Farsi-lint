/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Span } from '../../shared/types.ts';

/**
 * Finds all protected spans in text that should never be modified:
 * - URLs (http/https/ftp)
 * - Emails
 * - Fenced code blocks (```...```)
 * - Inline code (`...`)
 * - Social handles (@username)
 * - Hashtags (#tag)
 * - Version strings (e.g., v2.1.0, 1.0.4-beta)
 * - Latin words and alphanumeric runs (e.g., iPhone 15, HTML5, React, MP3)
 */
export function findProtectedSpans(text: string): Span[] {
  const spans: Span[] = [];

  // 1. Fenced Code Blocks: ```code```
  const codeBlockRegex = /```[\s\S]*?```/g;
  let match: RegExpExecArray | null;
  while ((match = codeBlockRegex.exec(text)) !== null) {
    spans.push({ start: match.index, end: match.index + match[0].length, type: 'code-block' });
  }

  // 2. Inline Code: `code`
  const inlineCodeRegex = /`[^`\n]+`/g;
  while ((match = inlineCodeRegex.exec(text)) !== null) {
    spans.push({ start: match.index, end: match.index + match[0].length, type: 'inline-code' });
  }

  // 3. URLs
  const urlRegex = /https?:\/\/[^\s<>"'{}|\\^`[\]]+/gi;
  while ((match = urlRegex.exec(text)) !== null) {
    spans.push({ start: match.index, end: match.index + match[0].length, type: 'url' });
  }

  // 4. Email addresses
  const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g;
  while ((match = emailRegex.exec(text)) !== null) {
    spans.push({ start: match.index, end: match.index + match[0].length, type: 'email' });
  }

  // 5. Mentions (@username)
  const mentionRegex = /@[A-Za-z0-9_]+/g;
  while ((match = mentionRegex.exec(text)) !== null) {
    spans.push({ start: match.index, end: match.index + match[0].length, type: 'mention' });
  }

  // 6. Hashtags (#tag)
  const hashtagRegex = /#[A-Za-z0-9_\u0600-\u06FF]+/g;
  while ((match = hashtagRegex.exec(text)) !== null) {
    spans.push({ start: match.index, end: match.index + match[0].length, type: 'hashtag' });
  }

  // 7. Version numbers (e.g., v2.1.0, 1.2.3)
  const versionRegex = /\bv?\d+(\.\d+)+(-[a-zA-Z0-9.]+)?\b/gi;
  while ((match = versionRegex.exec(text)) !== null) {
    spans.push({ start: match.index, end: match.index + match[0].length, type: 'version' });
  }

  // 8. Latin words and alphanumeric runs (e.g., iPhone 15 Pro, UTF8, MP3, React, CSS3)
  // Include words that contain Latin letters and may include digits or dashes
  const latinRunRegex = /\b[A-Za-z0-9]*[A-Za-z][A-Za-z0-9_-]*\b/g;
  while ((match = latinRunRegex.exec(text)) !== null) {
    spans.push({ start: match.index, end: match.index + match[0].length, type: 'latin-run' });
  }

  // Sort by start index and merge overlapping spans
  spans.sort((a, b) => a.start - b.start);
  const merged: Span[] = [];
  for (const span of spans) {
    if (merged.length === 0) {
      merged.push({ ...span });
      continue;
    }
    const last = merged[merged.length - 1];
    if (span.start <= last.end) {
      last.end = Math.max(last.end, span.end);
    } else {
      merged.push({ ...span });
    }
  }

  return merged;
}

/**
 * Checks if a candidate range [start, end) intersects any protected span.
 */
export function isSpanProtected(start: number, end: number, protectedSpans: Span[]): boolean {
  for (const p of protectedSpans) {
    // If range overlaps with [p.start, p.end)
    if (start < p.end && end > p.start) {
      return true;
    }
  }
  return false;
}

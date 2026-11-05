/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Issue, IssueSeverity } from '../../shared/types.ts';

const SEVERITY_WEIGHT: Record<IssueSeverity, number> = {
  error: 3,
  warning: 2,
  suggestion: 1,
};

/**
 * Detects overlapping issues.
 * When two issues overlap, keeps the one with higher severity and marks the other as conflict=true.
 */
export function detectConflicts(issues: Issue[]): Issue[] {
  // Clone issues
  const list: Issue[] = issues.map((i) => ({ ...i, conflict: false }));

  // Sort primarily by start offset, secondarily by severity descending
  list.sort((a, b) => {
    if (a.start !== b.start) return a.start - b.start;
    return SEVERITY_WEIGHT[b.severity] - SEVERITY_WEIGHT[a.severity];
  });

  for (let i = 0; i < list.length; i++) {
    const current = list[i];
    if (current.conflict) continue;

    for (let j = i + 1; j < list.length; j++) {
      const next = list[j];
      // Check if ranges overlap: [start, end)
      // Note: zero-width insertion (start === end) overlaps if it falls strictly inside another span
      const overlap = current.start < next.end && next.start < current.end;

      if (overlap) {
        if (SEVERITY_WEIGHT[current.severity] >= SEVERITY_WEIGHT[next.severity]) {
          next.conflict = true;
        } else {
          current.conflict = true;
          break;
        }
      }
    }
  }

  return list;
}

/**
 * Applies a set of accepted issues to the original text.
 * Sorts in descending order of start offset to preserve valid indices.
 * Ignores any issue marked as conflicting.
 */
export function applyIssues(text: string, issuesToApply: Issue[]): string {
  // Filter out conflicts or invalid spans
  const valid = issuesToApply.filter(
    (issue) => !issue.conflict && issue.start >= 0 && issue.end <= text.length && issue.start <= issue.end
  );

  // Sort descending by start offset
  valid.sort((a, b) => b.start - a.start || b.end - a.end);

  let result = text;
  for (const issue of valid) {
    const before = result.slice(0, issue.start);
    const after = result.slice(issue.end);
    result = before + issue.suggestion + after;
  }

  return result;
}

export interface DiffSegment {
  type: 'text' | 'issue';
  text: string;
  issue?: Issue;
  start?: number;
  end?: number;
}

/**
 * Breaks the original text into segments interleaved with issues for UI rendering.
 */
export function segmentTextWithIssues(text: string, issues: Issue[]): DiffSegment[] {
  const nonConflicting = issues
    .filter((i) => !i.conflict && i.start >= 0 && i.end <= text.length)
    .sort((a, b) => a.start - b.start);

  const segments: DiffSegment[] = [];
  let currentIndex = 0;

  for (const issue of nonConflicting) {
    if (issue.start > currentIndex) {
      segments.push({
        type: 'text',
        text: text.slice(currentIndex, issue.start),
      });
    }

    // If zero-width insertion
    if (issue.start === issue.end) {
      segments.push({
        type: 'issue',
        text: '⎵', // marker for zero-width insertion
        issue,
        start: issue.start,
        end: issue.end,
      });
      currentIndex = issue.end;
      continue;
    }

    segments.push({
      type: 'issue',
      text: text.slice(issue.start, issue.end),
      issue,
      start: issue.start,
      end: issue.end,
    });
    currentIndex = Math.max(currentIndex, issue.end);
  }

  if (currentIndex < text.length) {
    segments.push({
      type: 'text',
      text: text.slice(currentIndex),
    });
  }

  return segments;
}

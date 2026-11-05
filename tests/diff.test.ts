/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, it, expect } from 'vitest';
import { detectConflicts, applyIssues, segmentTextWithIssues } from '../src/core/diff/index.ts';
import { Issue } from '../src/shared/types.ts';

describe('Diff Engine (core/diff)', () => {
  it('applies non-overlapping issues in descending order', () => {
    const text = 'کتاب ها و قلم ها';
    const issues: Issue[] = [
      {
        id: '1',
        layer: 'local',
        category: 'نیم‌فاصله',
        severity: 'error',
        start: 0,
        end: 7,
        original: 'کتاب ها',
        suggestion: 'کتاب‌ها',
        explanation: 'نیم‌فاصله جمع',
      },
      {
        id: '2',
        layer: 'local',
        category: 'نیم‌فاصله',
        severity: 'error',
        start: 10,
        end: 16,
        original: 'قلم ها',
        suggestion: 'قلم‌ها',
        explanation: 'نیم‌فاصله جمع',
      },
    ];

    const result = applyIssues(text, issues);
    expect(result).toBe('کتاب‌ها و قلم‌ها');
  });

  it('detects overlapping spans and marks conflict on lower severity issue', () => {
    // Two overlapping issues at range [5, 15) and [10, 20)
    const issues: Issue[] = [
      {
        id: '1',
        layer: 'local',
        category: 'warning-cat',
        severity: 'warning',
        start: 5,
        end: 15,
        original: 'abcde12345',
        suggestion: 'fix1',
        explanation: 'test',
      },
      {
        id: '2',
        layer: 'llm',
        category: 'error-cat',
        severity: 'error',
        start: 10,
        end: 20,
        original: '12345vwxyz',
        suggestion: 'fix2',
        explanation: 'test error',
      },
    ];

    const resolved = detectConflicts(issues);
    const errorIssue = resolved.find((i) => i.id === '2');
    const warningIssue = resolved.find((i) => i.id === '1');

    expect(errorIssue?.conflict).toBe(false);
    expect(warningIssue?.conflict).toBe(true);
  });

  it('ignores conflicting issues when applying patches', () => {
    const text = 'Hello world from test';
    const issues: Issue[] = [
      {
        id: '1',
        layer: 'local',
        category: 'test',
        severity: 'error',
        start: 0,
        end: 5,
        original: 'Hello',
        suggestion: 'Salam',
        explanation: 'test',
        conflict: false,
      },
      {
        id: '2',
        layer: 'local',
        category: 'test',
        severity: 'warning',
        start: 3,
        end: 8,
        original: 'lo wo',
        suggestion: 'conflicted',
        explanation: 'test',
        conflict: true, // marked as conflict
      },
    ];

    const result = applyIssues(text, issues);
    expect(result).toBe('Salam world from test');
  });

  it('segments text correctly for UI rendering', () => {
    const text = 'متن اول، متن دوم';
    const issues: Issue[] = [
      {
        id: '1',
        layer: 'local',
        category: 'test',
        severity: 'error',
        start: 7,
        end: 8,
        original: '،',
        suggestion: '، ',
        explanation: 'فاصله',
      },
    ];

    const segments = segmentTextWithIssues(text, issues);
    expect(segments.length).toBe(3);
    expect(segments[0].text).toBe('متن اول');
    expect(segments[1].type).toBe('issue');
    expect(segments[2].text).toBe(' متن دوم');
  });
});

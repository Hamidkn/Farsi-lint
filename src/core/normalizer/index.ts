/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Issue, NormalizerOptions, DEFAULT_NORMALIZER_OPTIONS } from '../../shared/types.ts';
import { findProtectedSpans } from './protectedSpans.ts';
import {
  arabicCharsRule,
  persianDigitsRule,
  zwnjAffixesRule,
  cleanZwnjAndSpacesRule,
  punctuationMarksRule,
  quotesAndBracketsRule,
  kashidaAndEllipsisRule,
  ezafeStyleRule,
} from './rules.ts';

export * from './rules.ts';
export * from './protectedSpans.ts';

/**
 * Runs the local Persian normalizer rule pipeline.
 * Pure function: does not mutate the input text.
 * Each rule is toggleable via the options object.
 */
export function normalizePersianText(
  text: string,
  options: Partial<NormalizerOptions> = {}
): Issue[] {
  if (!text || text.trim().length === 0) {
    return [];
  }

  const mergedOptions: NormalizerOptions = {
    ...DEFAULT_NORMALIZER_OPTIONS,
    ...options,
  };

  const protectedSpans = findProtectedSpans(text);
  const allIssues: Issue[] = [];

  // Run enabled rules independently
  if (mergedOptions.arabicChars) {
    allIssues.push(...arabicCharsRule(text, mergedOptions, protectedSpans));
  }
  if (mergedOptions.cleanZwnjAndSpaces) {
    allIssues.push(...cleanZwnjAndSpacesRule(text, mergedOptions, protectedSpans));
  }
  if (mergedOptions.ezafeRule) {
    allIssues.push(...ezafeStyleRule(text, mergedOptions, protectedSpans));
  }
  if (mergedOptions.zwnjAffixes) {
    allIssues.push(...zwnjAffixesRule(text, mergedOptions, protectedSpans));
  }
  if (mergedOptions.punctuationMarks) {
    allIssues.push(...punctuationMarksRule(text, mergedOptions, protectedSpans));
  }
  if (mergedOptions.quotesAndBrackets) {
    allIssues.push(...quotesAndBracketsRule(text, mergedOptions, protectedSpans));
  }
  if (mergedOptions.kashidaAndEllipsis) {
    allIssues.push(...kashidaAndEllipsisRule(text, mergedOptions, protectedSpans));
  }
  if (mergedOptions.persianDigits) {
    allIssues.push(...persianDigitsRule(text, mergedOptions, protectedSpans));
  }

  // Sort by start offset ascending
  allIssues.sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start));

  // Deduplicate any exact overlapping spans from multiple rules
  const deduped: Issue[] = [];
  for (const issue of allIssues) {
    const isDup = deduped.some(
      (existing) =>
        existing.start === issue.start &&
        existing.end === issue.end &&
        existing.suggestion === issue.suggestion
    );
    if (!isDup) {
      deduped.push(issue);
    }
  }

  return deduped;
}

/**
 * Helper to calculate the percentage of Persian characters in a string.
 */
export function getPersianCharacterRatio(text: string): number {
  if (!text) return 0;
  const persianCharRegex = /[\u0600-\u06FF\uFB8A\u067E\u0686\u06AF\u200C]/g;
  const matches = text.match(persianCharRegex);
  if (!matches) return 0;
  // Non-whitespace character count
  const nonWsLength = text.replace(/\s+/g, '').length;
  if (nonWsLength === 0) return 0;
  return matches.length / nonWsLength;
}

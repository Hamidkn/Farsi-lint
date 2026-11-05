/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Issue, LLMIssueItem } from '../../shared/types.ts';

export interface TextChunk {
  index: number;
  text: string;
  startIndex: number; // offset in original full text
  endIndex: number;
  wordCount: number;
}

export const CATEGORY_LABELS_FA: Record<string, string> = {
  translationese: 'گرته‌برداری (ترجمه لفظی)',
  unnatural: 'بیان غیرطبیعی',
  grammar: 'دستور زبان و حروف اضافه',
  register: 'ناهماهنگی لحن (رسمی/محاوره)',
  collocation: 'ترکیب و همایندی نادرست',
  redundancy: 'حشو و حاشیه‌پردازی',
  terminology: 'ناهماهنگی اصطلاحات',
  clarity: 'ابهام و پیچیدگی جمله',
};

/**
 * Splits long text into chunks by paragraphs (aiming for ~1500 words per chunk).
 */
export function splitIntoChunks(text: string, maxWordsPerChunk = 1500): TextChunk[] {
  if (!text || text.trim().length === 0) {
    return [];
  }

  // Split by paragraph delimiters (\n\n or \n)
  const paragraphRegex = /(?:[^\n]+\n*)+/g;
  const chunks: TextChunk[] = [];

  let currentChunkText = '';
  let currentChunkStart = 0;
  let currentWords = 0;

  const countWords = (str: string) => str.trim().split(/\s+/).filter(Boolean).length;

  let match: RegExpExecArray | null;
  while ((match = paragraphRegex.exec(text)) !== null) {
    const para = match[0];
    const paraWords = countWords(para);

    if (currentWords > 0 && currentWords + paraWords > maxWordsPerChunk) {
      // Finalize current chunk
      chunks.push({
        index: chunks.length,
        text: currentChunkText,
        startIndex: currentChunkStart,
        endIndex: currentChunkStart + currentChunkText.length,
        wordCount: currentWords,
      });

      // Start new chunk
      currentChunkText = para;
      currentChunkStart = match.index;
      currentWords = paraWords;
    } else {
      if (currentWords === 0) {
        currentChunkStart = match.index;
      }
      currentChunkText += para;
      currentWords += paraWords;
    }
  }

  if (currentChunkText.length > 0) {
    chunks.push({
      index: chunks.length,
      text: currentChunkText,
      startIndex: currentChunkStart,
      endIndex: currentChunkStart + currentChunkText.length,
      wordCount: currentWords,
    });
  }

  return chunks;
}

/**
 * Locates verbatim quotes from the LLM in the chunk text, tracking occurrences
 * to handle duplicates correctly, and converting them into valid Issue objects.
 * Discards any quote not found verbatim.
 */
export function locateQuoteSpans(
  chunkText: string,
  rawIssues: LLMIssueItem[],
  chunkStartOffset: number = 0
): Issue[] {
  const issues: Issue[] = [];
  // Track cursor position for duplicate quotes to match in order of occurrence
  const quoteCursors: Record<string, number> = {};

  for (let i = 0; i < rawIssues.length; i++) {
    const item = rawIssues[i];
    const quote = item.quote.trim();
    if (!quote) continue;

    const fromIndex = quoteCursors[quote] ?? 0;
    const foundIdx = chunkText.indexOf(quote, fromIndex);

    if (foundIdx === -1) {
      // Try searching from the beginning once if cursor was advanced
      if (fromIndex > 0) {
        const retryIdx = chunkText.indexOf(quote, 0);
        if (retryIdx !== -1) {
          quoteCursors[quote] = retryIdx + quote.length;
          issues.push(createIssue(item, retryIdx + chunkStartOffset, quote, i));
        }
      }
      // If still not found verbatim, discard per requirement!
      continue;
    }

    quoteCursors[quote] = foundIdx + quote.length;
    issues.push(createIssue(item, foundIdx + chunkStartOffset, quote, i));
  }

  return issues;
}

function createIssue(
  item: LLMIssueItem,
  start: number,
  exactQuote: string,
  index: number
): Issue {
  const categoryLabel = CATEGORY_LABELS_FA[item.category] || item.category;

  return {
    id: `llm-${start}-${index}`,
    layer: 'llm',
    category: categoryLabel,
    severity: item.severity,
    start,
    end: start + exactQuote.length,
    original: exactQuote,
    suggestion: item.suggestion,
    explanation: item.explanation_fa,
  };
}

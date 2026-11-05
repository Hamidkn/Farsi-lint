/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Issue, LLMSettings } from '../../shared/types.ts';
import { splitIntoChunks, locateQuoteSpans } from './chunker.ts';
import { executeLLMReview } from './adapters.ts';

export * from './reviewPrompt.ts';
export * from './schema.ts';
export * from './chunker.ts';
export * from './adapters.ts';

export interface FullLLMReviewResult {
  issues: Issue[];
  summaryFa: string;
  aiLikelihoodNoteFa: string;
}

/**
 * High-level function to review Persian text with LLM:
 * 1. Splits text into chunks by paragraphs (~1500 words each).
 * 2. Runs review per chunk, carrying established terminology across chunks.
 * 3. Maps returned verbatim quotes back to exact character offsets.
 * 4. Combines issues and summary notes.
 */
export async function reviewPersianTextWithLLM(
  text: string,
  settings: LLMSettings
): Promise<FullLLMReviewResult> {
  if (!text || text.trim().length === 0) {
    return {
      issues: [],
      summaryFa: 'متنی برای بررسی ارائه نشده است.',
      aiLikelihoodNoteFa: '',
    };
  }

  const chunks = splitIntoChunks(text, 1500);
  const allIssues: Issue[] = [];
  const summaries: string[] = [];
  const aiNotes: string[] = [];
  const establishedTerminology: string[] = [];

  for (const chunk of chunks) {
    const response = await executeLLMReview({
      settings,
      textToReview: chunk.text,
      contextTerminology: establishedTerminology,
    });

    if (response.summary_fa) {
      summaries.push(response.summary_fa);
    }
    if (response.ai_likelihood_note_fa) {
      aiNotes.push(response.ai_likelihood_note_fa);
    }

    // Collect any terminology suggestions to maintain consistency in subsequent chunks
    for (const item of response.issues) {
      if (item.category === 'terminology') {
        establishedTerminology.push(`«${item.quote}» -> «${item.suggestion}»`);
      }
    }

    // Map quotes to exact spans within this chunk
    const chunkIssues = locateQuoteSpans(chunk.text, response.issues, chunk.startIndex);
    allIssues.push(...chunkIssues);
  }

  return {
    issues: allIssues,
    summaryFa: summaries.join('\n\n'),
    aiLikelihoodNoteFa: aiNotes.filter(Boolean).join(' '),
  };
}

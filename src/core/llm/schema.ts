/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { z } from 'zod';

export const LLMIssueItemSchema = z.object({
  quote: z.string().min(1, 'Quote must not be empty'),
  category: z.enum([
    'translationese',
    'unnatural',
    'grammar',
    'register',
    'collocation',
    'redundancy',
    'terminology',
    'clarity',
  ]),
  severity: z.enum(['error', 'warning', 'suggestion']),
  suggestion: z.string(),
  explanation_fa: z.string(),
});

export const LLMReviewResponseSchema = z.object({
  issues: z.array(LLMIssueItemSchema),
  summary_fa: z.string(),
  ai_likelihood_note_fa: z.string().optional().default(''),
});

export type ValidatedLLMReview = z.infer<typeof LLMReviewResponseSchema>;

/**
 * Parses raw JSON string returned by the LLM, stripping markdown fences if present,
 * and validates it against the zod schema.
 */
export function validateLLMJson(rawText: string): { success: true; data: ValidatedLLMReview } | { success: false; error: string } {
  try {
    let clean = rawText.trim();
    // Strip markdown code fences: ```json ... ``` or ``` ... ```
    if (clean.startsWith('```')) {
      clean = clean.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim();
    }

    const parsed = JSON.parse(clean);
    const result = LLMReviewResponseSchema.safeParse(parsed);

    if (result.success) {
      return { success: true, data: result.data };
    } else {
      const issueDetails = result.error.issues.map((i) => `${i.path.join('.')}: ${i.message}`).join(', ');
      return { success: false, error: `Schema validation failed: ${issueDetails}` };
    }
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return { success: false, error: `JSON parse error: ${message}` };
  }
}

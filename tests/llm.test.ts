/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { validateLLMJson } from '../src/core/llm/schema.ts';
import { splitIntoChunks, locateQuoteSpans } from '../src/core/llm/chunker.ts';
import { executeLLMReview } from '../src/core/llm/adapters.ts';
import { LLMSettings } from '../src/shared/types.ts';

describe('LLM Review Layer (core/llm)', () => {
  describe('Zod Schema Validation', () => {
    it('validates a correct structured JSON response', () => {
      const validJson = JSON.stringify({
        issues: [
          {
            quote: 'در پایان روز',
            category: 'translationese',
            severity: 'error',
            suggestion: 'در نهایت',
            explanation_fa: 'گرته‌برداری از عبارت انگلیسی at the end of the day',
          },
        ],
        summary_fa: 'متن دارای گرته‌برداری‌های آشکار از زبان انگلیسی است.',
        ai_likelihood_note_fa: 'نشانه‌های ترجمه ماشینی در چیدمان کلمات مشهود است.',
      });

      const result = validateLLMJson(validJson);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.issues.length).toBe(1);
        expect(result.data.issues[0].category).toBe('translationese');
      }
    });

    it('strips markdown code blocks (```json ... ```)', () => {
      const markdownJson = `\`\`\`json
{
  "issues": [],
  "summary_fa": "متن بدون مشکل نگارشی است.",
  "ai_likelihood_note_fa": ""
}
\`\`\``;

      const result = validateLLMJson(markdownJson);
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.issues.length).toBe(0);
      }
    });

    it('rejects invalid JSON structure', () => {
      const invalidJson = '{"issues": "not an array"}';
      const result = validateLLMJson(invalidJson);
      expect(result.success).toBe(false);
    });

    it('rejects unknown category values', () => {
      const badCategoryJson = JSON.stringify({
        issues: [
          {
            quote: 'تست',
            category: 'unknown_category',
            severity: 'error',
            suggestion: 'آزمون',
            explanation_fa: 'توضیح',
          },
        ],
        summary_fa: 'خلاصه',
      });
      const result = validateLLMJson(badCategoryJson);
      expect(result.success).toBe(false);
    });
  });

  describe('Chunker & Verbatim Quote Locator', () => {
    it('splits text into chunks by paragraphs preserving bounds', () => {
      const text = 'پاراگراف اول.\n\nپاراگراف دوم.\n\nپاراگراف سوم.';
      const chunks = splitIntoChunks(text, 2);
      expect(chunks.length).toBeGreaterThanOrEqual(2);
      expect(chunks[0].text).toContain('پاراگراف');
    });

    it('locates verbatim quotes and calculates exact character offsets', () => {
      const text = 'ما باید تصمیم بسازیم و به خانه برویم.';
      const rawIssues = [
        {
          quote: 'تصمیم بسازیم',
          category: 'collocation' as const,
          severity: 'error' as const,
          suggestion: 'تصمیم بگیریم',
          explanation_fa: 'همایندی نادرست فعل ساختن با تصمیم',
        },
      ];

      const issues = locateQuoteSpans(text, rawIssues);
      expect(issues.length).toBe(1);
      expect(issues[0].original).toBe('تصمیم بسازیم');
      expect(issues[0].start).toBe(8);
      expect(issues[0].end).toBe(20);
      expect(text.slice(issues[0].start, issues[0].end)).toBe('تصمیم بسازیم');
    });

    it('CRITICAL: discards issues whose quotes are NOT found verbatim in text', () => {
      const text = 'این یک متن معمولی و کاملاً درست است.';
      const rawIssues = [
        {
          quote: 'عبارت خیالی که وجود ندارد',
          category: 'hallucination' as any,
          severity: 'warning' as const,
          suggestion: 'اصلاح',
          explanation_fa: 'توضیح',
        },
      ];

      const issues = locateQuoteSpans(text, rawIssues);
      expect(issues.length).toBe(0);
    });

    it('handles duplicate occurrences of the same quote by order of appearance', () => {
      const text = 'این یک خطا است و باز هم این یک خطا است در پایان.';
      const rawIssues = [
        {
          quote: 'این یک خطا است',
          category: 'redundancy' as const,
          severity: 'suggestion' as const,
          suggestion: 'خطاست',
          explanation_fa: 'اول',
        },
        {
          quote: 'این یک خطا است',
          category: 'redundancy' as const,
          severity: 'suggestion' as const,
          suggestion: 'خطاست',
          explanation_fa: 'دوم',
        },
      ];

      const issues = locateQuoteSpans(text, rawIssues);
      expect(issues.length).toBe(2);
      expect(issues[0].start).toBe(0);
      expect(issues[1].start).toBe(24);
      expect(issues[0].start).toBeLessThan(issues[1].start);
    });
  });

  describe('Mocked Provider Adapters & Retries', () => {
    const originalFetch = globalThis.fetch;

    beforeEach(() => {
      vi.restoreAllMocks();
    });

    afterEach(() => {
      globalThis.fetch = originalFetch;
    });

    it('executes Anthropic adapter and parses structured output', async () => {
      const mockResponse = {
        content: [
          {
            text: JSON.stringify({
              issues: [
                {
                  quote: 'در پایان روز',
                  category: 'translationese',
                  severity: 'error',
                  suggestion: 'در نهایت',
                  explanation_fa: 'گرته‌برداری',
                },
              ],
              summary_fa: 'ترجمه ماشینی',
              ai_likelihood_note_fa: 'احتمال بالا',
            }),
          },
        ],
      };

      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      } as Response);

      const settings: LLMSettings = {
        provider: 'anthropic',
        apiKey: 'test-anthropic-key',
        model: 'claude-3-5-sonnet-20241022',
      };

      const result = await executeLLMReview({
        settings,
        textToReview: 'در پایان روز تصمیم گرفتیم.',
      });

      expect(result.issues.length).toBe(1);
      expect(result.summary_fa).toBe('ترجمه ماشینی');
    });

    it('retries once if LLM returns invalid JSON on first attempt', async () => {
      let callCount = 0;
      globalThis.fetch = vi.fn().mockImplementation(async () => {
        callCount++;
        if (callCount === 1) {
          return {
            ok: true,
            json: async () => ({
              choices: [{ message: { content: 'Sorry, here is the result: { invalid' } }],
            }),
          } as Response;
        }
        return {
          ok: true,
          json: async () => ({
            choices: [
              {
                message: {
                  content: JSON.stringify({
                    issues: [],
                    summary_fa: 'متن بازبینی شد.',
                    ai_likelihood_note_fa: '',
                  }),
                },
              },
            ],
          }),
        } as Response;
      });

      const settings: LLMSettings = {
        provider: 'openai',
        apiKey: 'test-openai-key',
        model: 'gpt-4o-mini',
      };

      const result = await executeLLMReview({
        settings,
        textToReview: 'متن نمونه',
      });

      expect(callCount).toBe(2);
      expect(result.summary_fa).toBe('متن بازبینی شد.');
    });
  });
});

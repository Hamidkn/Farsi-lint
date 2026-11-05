/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export type Layer = 'local' | 'llm';

export type IssueSeverity = 'error' | 'warning' | 'suggestion';

export interface Issue {
  id: string;
  layer: Layer;
  ruleId?: string; // for local rules (e.g. 'arabic-chars', 'zwnj-affixes')
  category: string; // e.g. 'orthography', 'typography', 'translationese', 'grammar', etc.
  severity: IssueSeverity;
  start: number;
  end: number; // offsets in the original text
  original: string;
  suggestion: string;
  explanation: string; // Persian explanation
  conflict?: boolean; // if it overlaps with a higher-priority issue
}

export interface Span {
  start: number;
  end: number;
  type?: string;
}

export interface NormalizerOptions {
  arabicChars: boolean;          // ي/ك → ی/ک
  persianDigits: boolean;        // Arabic-Indic & English digits → Persian digits (outside protected spans)
  zwnjAffixes: boolean;          // می/نمی, ها/های, تر/ترین, ام/ای/ایم/اید/اند after ه, etc.
  cleanZwnjAndSpaces: boolean;   // remove redundant ZWNJ next to space, collapse multiple spaces
  punctuationMarks: boolean;     // , ; ? → ، ؛ ؟, proper spacing around punctuation
  quotesAndBrackets: boolean;    // quotes → «», spacing around brackets
  kashidaAndEllipsis: boolean;   // ... → …, remove kashida ـ
  ezafeRule: boolean;            // "ه ی" → "هٔ" or "هی"
  ezafeStyle: 'hamza' | 'ye';    // 'hamza' (هٔ) or 'ye' (هی / خانه‌ی)
}

export const DEFAULT_NORMALIZER_OPTIONS: NormalizerOptions = {
  arabicChars: true,
  persianDigits: true,
  zwnjAffixes: true,
  cleanZwnjAndSpaces: true,
  punctuationMarks: true,
  quotesAndBrackets: true,
  kashidaAndEllipsis: true,
  ezafeRule: true,
  ezafeStyle: 'hamza',
};

export type LLMProvider = 'anthropic' | 'openai' | 'openrouter' | 'custom' | 'gemini';

export interface LLMSettings {
  provider: LLMProvider;
  apiKey: string;
  model: string;
  customEndpoint?: string;
  customReviewPrompt?: string;
}

export const DEFAULT_LLM_SETTINGS: LLMSettings = {
  provider: 'gemini',
  apiKey: '',
  model: 'gemini-2.5-flash',
  customEndpoint: '',
  customReviewPrompt: '',
};

export interface ExtensionSettings {
  normalizer: NormalizerOptions;
  llm: LLMSettings;
  disabledSites: string[];
  autoUnderline: boolean;
  floatingButton: boolean;
}

export const DEFAULT_SETTINGS: ExtensionSettings = {
  normalizer: DEFAULT_NORMALIZER_OPTIONS,
  llm: DEFAULT_LLM_SETTINGS,
  disabledSites: ['bank', 'login', 'payment'],
  autoUnderline: true,
  floatingButton: true,
};

export interface LLMIssueItem {
  quote: string;
  category: 'translationese' | 'unnatural' | 'grammar' | 'register' | 'collocation' | 'redundancy' | 'terminology' | 'clarity';
  severity: IssueSeverity;
  suggestion: string;
  explanation_fa: string;
}

export interface LLMReviewResponse {
  issues: LLMIssueItem[];
  summary_fa: string;
  ai_likelihood_note_fa?: string;
}

export interface ReviewState {
  text: string;
  issues: Issue[];
  summary?: string;
  aiLikelihoodNote?: string;
  status: 'idle' | 'normalizing' | 'reviewing-llm' | 'completed' | 'error';
  errorMessage?: string;
}

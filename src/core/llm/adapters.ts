/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { LLMSettings, LLMReviewResponse } from '../../shared/types.ts';
import { validateLLMJson } from './schema.ts';
import { DEFAULT_REVIEW_SYSTEM_PROMPT } from './reviewPrompt.ts';

export interface LLMAdapterRequest {
  settings: LLMSettings;
  textToReview: string;
  contextTerminology?: string[];
  isRetry?: boolean;
  previousError?: string;
}

/**
 * Dispatches the review request to the appropriate LLM provider.
 */
export async function executeLLMReview(request: LLMAdapterRequest): Promise<LLMReviewResponse> {
  const { settings, textToReview, contextTerminology = [], isRetry = false, previousError } = request;

  if (!settings.apiKey && settings.provider !== 'custom') {
    throw new Error('کلید دسترسی (API Key) وارد نشده است. لطفاً در تنظیمات افزونه کلید خود را وارد کنید.');
  }

  const systemPrompt = settings.customReviewPrompt?.trim() || DEFAULT_REVIEW_SYSTEM_PROMPT;

  let userContent = `Review the following Persian text:\n\n"""\n${textToReview}\n"""`;
  if (contextTerminology.length > 0) {
    userContent += `\n\nContext - Previously established terminology:\n${contextTerminology.join('\n')}`;
  }

  if (isRetry && previousError) {
    userContent += `\n\nCRITICAL FIX: Your previous response was invalid JSON or did not conform to the schema: "${previousError}". Output ONLY raw valid JSON conforming strictly to the requested schema.`;
  }

  let rawResponseText = '';

  switch (settings.provider) {
    case 'anthropic':
      rawResponseText = await callAnthropic(settings, systemPrompt, userContent);
      break;

    case 'openai':
    case 'openrouter':
    case 'custom':
      rawResponseText = await callOpenAICompatible(settings, systemPrompt, userContent);
      break;

    case 'gemini':
      rawResponseText = await callGemini(settings, systemPrompt, userContent);
      break;

    default:
      throw new Error(`سرویس‌دهنده ناشناخته: ${settings.provider}`);
  }

  // Validate output with Zod
  const validation = validateLLMJson(rawResponseText);
  if (validation.success) {
    return validation.data;
  }

  // If validation failed and we haven't retried yet, retry once with repair prompt
  if (!isRetry) {
    return executeLLMReview({
      ...request,
      isRetry: true,
      previousError: validation.error,
    });
  }

  throw new Error(`خطا در قالب پاسخ هوش مصنوعی: ${validation.error}`);
}

/**
 * Anthropic Claude Adapter
 */
async function callAnthropic(
  settings: LLMSettings,
  systemPrompt: string,
  userContent: string
): Promise<string> {
  const endpoint = 'https://api.anthropic.com/v1/messages';
  const model = settings.model || 'claude-3-5-sonnet-20241022';

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': settings.apiKey,
      'anthropic-version': '2023-06-01',
      'dangerously-allow-browser': 'true',
    },
    body: JSON.stringify({
      model,
      system: systemPrompt,
      max_tokens: 4096,
      messages: [{ role: 'user', content: userContent }],
    }),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`خطای سرویس Anthropic (${res.status}): ${errorText.slice(0, 200)}`);
  }

  const data = await res.json();
  const text = data?.content?.[0]?.text;
  if (!text) {
    throw new Error('پاسخ معتبری از سرور Anthropic دریافت نشد.');
  }
  return text;
}

/**
 * OpenAI, OpenRouter, and generic OpenAI-compatible endpoint (Ollama, LM Studio)
 */
async function callOpenAICompatible(
  settings: LLMSettings,
  systemPrompt: string,
  userContent: string
): Promise<string> {
  let endpoint = 'https://api.openai.com/v1/chat/completions';
  let defaultModel = 'gpt-4o-mini';

  if (settings.provider === 'openrouter') {
    endpoint = 'https://openrouter.ai/api/v1/chat/completions';
    defaultModel = 'anthropic/claude-3.5-sonnet';
  } else if (settings.provider === 'custom') {
    endpoint = settings.customEndpoint || 'http://localhost:11434/v1/chat/completions';
    defaultModel = 'llama3.3:70b';
  }

  const model = settings.model || defaultModel;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (settings.apiKey) {
    headers['Authorization'] = `Bearer ${settings.apiKey}`;
  }

  if (settings.provider === 'openrouter') {
    headers['HTTP-Referer'] = 'https://farsi-lint.extension';
    headers['X-Title'] = 'Farsi-lint Extension';
  }

  const res = await fetch(endpoint, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      model,
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userContent },
      ],
      temperature: 0.1,
    }),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`خطای سرویس هوش مصنوعی (${res.status}): ${errorText.slice(0, 200)}`);
  }

  const data = await res.json();
  const text = data?.choices?.[0]?.message?.content;
  if (!text) {
    throw new Error('پاسخ معتبری از مدل هوش مصنوعی دریافت نشد.');
  }
  return text;
}

/**
 * Google Gemini Adapter (OpenAI-compatible endpoint or Gemini v1beta)
 */
async function callGemini(
  settings: LLMSettings,
  systemPrompt: string,
  userContent: string
): Promise<string> {
  const model = settings.model || 'gemini-2.5-flash';
  const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(settings.apiKey)}`;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      systemInstruction: {
        parts: [{ text: systemPrompt }],
      },
      contents: [
        {
          role: 'user',
          parts: [{ text: userContent }],
        },
      ],
      generationConfig: {
        responseMimeType: 'application/json',
        temperature: 0.1,
      },
    }),
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => '');
    throw new Error(`خطای سرویس Gemini (${res.status}): ${errorText.slice(0, 200)}`);
  }

  const data = await res.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) {
    throw new Error('پاسخ معتبری از سرور Gemini دریافت نشد.');
  }
  return text;
}

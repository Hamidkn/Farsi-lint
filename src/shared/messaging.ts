/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Issue, LLMSettings, NormalizerOptions } from './types.ts';

export type ExtensionMessage =
  | { type: 'OPEN_SIDE_PANEL'; text: string }
  | { type: 'REQUEST_LOCAL_NORMALIZE'; text: string; options?: Partial<NormalizerOptions> }
  | { type: 'RESPONSE_LOCAL_NORMALIZE'; issues: Issue[] }
  | { type: 'REQUEST_LLM_REVIEW'; text: string; settings?: LLMSettings }
  | { type: 'RESPONSE_LLM_REVIEW'; issues: Issue[]; summaryFa: string; aiLikelihoodNoteFa: string }
  | { type: 'APPLY_FIX'; issue: Issue }
  | { type: 'ERROR'; message: string };

/**
 * Sends a message to the Chrome extension background worker or active tab.
 */
export async function sendExtensionMessage<T = unknown>(message: ExtensionMessage): Promise<T | null> {
  if (typeof chrome !== 'undefined' && chrome.runtime?.sendMessage) {
    try {
      return await chrome.runtime.sendMessage(message);
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { normalizePersianText } from '../core/normalizer/index.ts';
import { reviewPersianTextWithLLM } from '../core/llm/index.ts';
import { loadSettings } from '../shared/storage.ts';
import { ExtensionMessage } from '../shared/messaging.ts';

// Set up Context Menus on extension installation
if (typeof chrome !== 'undefined' && chrome.runtime?.onInstalled) {
  chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
      id: 'farsi-lint-review',
      title: 'بازبینی متن فارسی با فارسی‌لینت',
      contexts: ['selection', 'editable'],
    });
  });
}

// Handle Context Menu clicks
if (typeof chrome !== 'undefined' && chrome.contextMenus?.onClicked) {
  chrome.contextMenus.onClicked.addListener(async (info: chrome.contextMenus.OnClickData, tab?: chrome.tabs.Tab) => {
    if (info.menuItemId === 'farsi-lint-review' && tab?.id) {
      const selectedText = info.selectionText || '';
      if (chrome.sidePanel?.open) {
        await chrome.sidePanel.open({ tabId: tab.id });
      }
      if (selectedText) {
        chrome.tabs.sendMessage(tab.id, {
          type: 'OPEN_SIDE_PANEL',
          text: selectedText,
        });
      }
    }
  });
}

// Handle Keyboard Commands (Ctrl+Shift+Y / Command+Shift+Y)
if (typeof chrome !== 'undefined' && chrome.commands?.onCommand) {
  chrome.commands.onCommand.addListener(async (command: string, tab?: chrome.tabs.Tab) => {
    if (command === 'review-persian-text' && tab?.id) {
      if (chrome.sidePanel?.open) {
        await chrome.sidePanel.open({ tabId: tab.id });
      }
      chrome.tabs.sendMessage(tab.id, {
        type: 'TRIGGER_SELECTION_REVIEW',
      });
    }
  });
}

// Message routing
if (typeof chrome !== 'undefined' && chrome.runtime?.onMessage) {
  chrome.runtime.onMessage.addListener((message: ExtensionMessage, _sender: chrome.runtime.MessageSender, sendResponse: (res?: unknown) => void) => {
    handleMessage(message).then(sendResponse);
    return true; // Keep channel open for async response
  });
}

async function handleMessage(message: ExtensionMessage) {
  try {
    if (message.type === 'REQUEST_LOCAL_NORMALIZE') {
      const settings = await loadSettings();
      const issues = normalizePersianText(message.text, message.options || settings.normalizer);
      return { success: true, issues };
    }

    if (message.type === 'REQUEST_LLM_REVIEW') {
      const settings = await loadSettings();
      const activeLLMSettings = message.settings || settings.llm;
      const result = await reviewPersianTextWithLLM(message.text, activeLLMSettings);
      return { success: true, ...result };
    }

    return { success: true };
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    return { success: false, error: errorMsg };
  }
}

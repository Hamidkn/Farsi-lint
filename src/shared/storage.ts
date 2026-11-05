/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { ExtensionSettings, DEFAULT_SETTINGS } from './types.ts';

const SETTINGS_KEY = 'farsi_lint_settings';

/**
 * Checks if running inside an actual Chrome Extension runtime.
 */
function isChromeExtension(): boolean {
  return typeof chrome !== 'undefined' && !!chrome?.storage?.local;
}

/**
 * Loads extension settings from chrome.storage.local (or localStorage in web preview).
 */
export async function loadSettings(): Promise<ExtensionSettings> {
  if (isChromeExtension()) {
    try {
      const result = await chrome.storage.local.get([SETTINGS_KEY]);
      if (result && result[SETTINGS_KEY]) {
        return mergeWithDefaults(result[SETTINGS_KEY]);
      }
    } catch {
      // Fallback to defaults
    }
  } else {
    try {
      const raw = localStorage.getItem(SETTINGS_KEY);
      if (raw) {
        return mergeWithDefaults(JSON.parse(raw));
      }
    } catch {
      // Fallback
    }
  }

  return DEFAULT_SETTINGS;
}

/**
 * Saves extension settings to chrome.storage.local (never sync, to keep API keys secure).
 */
export async function saveSettings(settings: ExtensionSettings): Promise<void> {
  if (isChromeExtension()) {
    try {
      await chrome.storage.local.set({ [SETTINGS_KEY]: settings });
      return;
    } catch {
      // Fallback below
    }
  }

  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch {
    // Ignore storage quota errors
  }
}

function mergeWithDefaults(custom: Partial<ExtensionSettings>): ExtensionSettings {
  return {
    ...DEFAULT_SETTINGS,
    ...custom,
    normalizer: {
      ...DEFAULT_SETTINGS.normalizer,
      ...(custom.normalizer || {}),
    },
    llm: {
      ...DEFAULT_SETTINGS.llm,
      ...(custom.llm || {}),
    },
    disabledSites: custom.disabledSites || DEFAULT_SETTINGS.disabledSites,
  };
}

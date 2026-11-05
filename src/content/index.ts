/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { normalizePersianText, getPersianCharacterRatio } from '../core/normalizer/index.ts';
import { loadSettings } from '../shared/storage.ts';
import { Issue } from '../shared/types.ts';

let activeElement: HTMLElement | null = null;
let debounceTimer: ReturnType<typeof setTimeout> | null = null;
let floatingBtn: HTMLElement | null = null;
let tooltipElement: HTMLElement | null = null;
let overlayContainer: HTMLElement | null = null;
let currentIssues: Issue[] = [];

/**
 * Initializes the content script.
 */
export function initContentScript() {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  // Check if disabled on current domain or Google Docs
  const hostname = window.location.hostname || '';
  if (hostname.includes('docs.google.com')) {
    initGoogleDocsNotice();
    return;
  }

  // Listen to focus, blur, and input events
  document.addEventListener('focusin', handleFocusIn);
  document.addEventListener('focusout', handleFocusOut);
  document.addEventListener('input', handleInput);
  window.addEventListener('resize', updateOverlayPositions);
  window.addEventListener('scroll', updateOverlayPositions, true);

  // Listen to runtime messages from background (e.g. context menu or keyboard shortcuts)
  if (typeof chrome !== 'undefined' && chrome.runtime?.onMessage) {
    chrome.runtime.onMessage.addListener((message: { type?: string }) => {
      if (message.type === 'TRIGGER_SELECTION_REVIEW') {
        const selected = window.getSelection()?.toString() || getActiveElementText();
        if (selected) {
          chrome.runtime.sendMessage({ type: 'OPEN_SIDE_PANEL', text: selected });
        }
      }
    });
  }
}

function initGoogleDocsNotice() {
  // If user selects text in Google Docs, show friendly guidance
  document.addEventListener('mouseup', () => {
    const sel = window.getSelection()?.toString();
    if (sel && getPersianCharacterRatio(sel) > 0.3) {
      showFloatingButton(
        window.innerWidth / 2,
        window.innerHeight - 80,
        'متن اسناد گوگل بر بوم Canvas اجرا می‌شود؛ متن را در پنل کناری کپی کنید',
        () => {
          if (typeof chrome !== 'undefined' && chrome.runtime?.sendMessage) {
            chrome.runtime.sendMessage({ type: 'OPEN_SIDE_PANEL', text: sel });
          }
        }
      );
    }
  });
}

function handleFocusIn(e: FocusEvent) {
  const target = e.target as HTMLElement;
  if (!isEligibleEditable(target)) return;

  activeElement = target;
  checkTextAndRun(target);
}

function handleFocusOut(e: FocusEvent) {
  // Delay clearing to allow clicking floating button or tooltip
  setTimeout(() => {
    if (
      document.activeElement !== activeElement &&
      !tooltipElement?.contains(document.activeElement)
    ) {
      hideFloatingButton();
    }
  }, 250);
}

function handleInput(e: Event) {
  const target = e.target as HTMLElement;
  if (!isEligibleEditable(target)) return;

  activeElement = target;
  if (debounceTimer) clearTimeout(debounceTimer);

  debounceTimer = setTimeout(() => {
    checkTextAndRun(target);
  }, 400);
}

/**
 * Checks if target is an editable field and not a sensitive password/banking field.
 */
function isEligibleEditable(el: HTMLElement | null): boolean {
  if (!el) return false;

  // Sensitive field detection
  if (el.tagName === 'INPUT') {
    const input = el as HTMLInputElement;
    if (input.type === 'password' || input.autocomplete?.includes('cc-')) {
      return false;
    }
    return input.type === 'text' || input.type === 'search' || !input.type;
  }

  if (el.tagName === 'TEXTAREA') return true;
  if (el.isContentEditable) return true;

  return false;
}

function getElementText(el: HTMLElement): string {
  if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
    return (el as HTMLInputElement | HTMLTextAreaElement).value;
  }
  return el.innerText || el.textContent || '';
}

function getActiveElementText(): string {
  if (!activeElement) return '';
  return getElementText(activeElement);
}

async function checkTextAndRun(el: HTMLElement) {
  const text = getElementText(el);
  const ratio = getPersianCharacterRatio(text);

  // Load user settings
  const settings = await loadSettings();

  // Check disabled site list
  const currentHost = window.location.hostname || '';
  if (settings.disabledSites.some((site) => currentHost.includes(site))) {
    removeOverlay();
    hideFloatingButton();
    return;
  }

  // Must have >30% Persian characters
  if (ratio < 0.3 || text.trim().length === 0) {
    removeOverlay();
    hideFloatingButton();
    return;
  }

  // Show floating button
  if (settings.floatingButton) {
    positionFloatingButtonForElement(el);
  }

  // Run local normalizer for inline underlines
  if (settings.autoUnderline) {
    currentIssues = normalizePersianText(text, settings.normalizer);
    renderUnderlineOverlay(el, currentIssues);
  } else {
    removeOverlay();
  }
}

function positionFloatingButtonForElement(el: HTMLElement) {
  const rect = el.getBoundingClientRect();
  const left = rect.right - 140;
  const top = rect.bottom + 6;

  showFloatingButton(
    Math.max(10, left),
    top,
    'بازبینی با فارسی‌لینت',
    () => {
      const text = getElementText(el);
      if (typeof chrome !== 'undefined' && chrome.runtime?.sendMessage) {
        chrome.runtime.sendMessage({ type: 'OPEN_SIDE_PANEL', text });
      }
    }
  );
}

function showFloatingButton(x: number, y: number, label: string, onClick: () => void) {
  if (!floatingBtn) {
    floatingBtn = document.createElement('button');
    floatingBtn.className = 'farsi-lint-floating-btn';
    document.body.appendChild(floatingBtn);
  }

  floatingBtn.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M12 20h9"/>
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
    </svg>
    <span>${label}</span>
  `;

  floatingBtn.style.left = `${Math.min(window.innerWidth - 160, Math.max(10, x))}px`;
  floatingBtn.style.top = `${y}px`;
  floatingBtn.style.display = 'flex';

  floatingBtn.onclick = (e) => {
    e.preventDefault();
    e.stopPropagation();
    onClick();
  };
}

function hideFloatingButton() {
  if (floatingBtn) {
    floatingBtn.style.display = 'none';
  }
}

/**
 * Renders wavy underlines overlay without modifying the DOM of the editor itself.
 */
function renderUnderlineOverlay(el: HTMLElement, issues: Issue[]) {
  removeOverlay();

  if (issues.length === 0) return;

  const rect = el.getBoundingClientRect();
  overlayContainer = document.createElement('div');
  overlayContainer.className = 'farsi-lint-overlay-container';
  overlayContainer.style.left = `${rect.left + window.scrollX}px`;
  overlayContainer.style.top = `${rect.top + window.scrollY}px`;
  overlayContainer.style.width = `${rect.width}px`;
  overlayContainer.style.height = `${rect.height}px`;

  document.body.appendChild(overlayContainer);

  // Position highlights
  for (const issue of issues) {
    const coords = calculateSpanCoordinates(el, issue.start, issue.end);
    if (!coords) continue;

    const highlight = document.createElement('span');
    highlight.className = `farsi-lint-highlight severity-${issue.severity}`;
    highlight.style.left = `${coords.x}px`;
    highlight.style.top = `${coords.y}px`;
    highlight.style.width = `${Math.max(8, coords.width)}px`;
    highlight.style.height = `${Math.max(16, coords.height)}px`;

    highlight.onmouseenter = (e) => showTooltip(e, issue, el);
    highlight.onmouseleave = () => scheduleHideTooltip();

    overlayContainer.appendChild(highlight);
  }
}

function updateOverlayPositions() {
  if (activeElement && overlayContainer) {
    const rect = activeElement.getBoundingClientRect();
    overlayContainer.style.left = `${rect.left + window.scrollX}px`;
    overlayContainer.style.top = `${rect.top + window.scrollY}px`;
    overlayContainer.style.width = `${rect.width}px`;
    overlayContainer.style.height = `${rect.height}px`;
  }
}

function removeOverlay() {
  if (overlayContainer) {
    overlayContainer.remove();
    overlayContainer = null;
  }
  hideTooltip();
}

/**
 * Calculates span bounding coordinates for textarea or contenteditable element.
 */
function calculateSpanCoordinates(
  el: HTMLElement,
  start: number,
  end: number
): { x: number; y: number; width: number; height: number } | null {
  if (el.isContentEditable) {
    return calculateContentEditableCoordinates(el, start, end);
  }
  return calculateInputCoordinates(el as HTMLInputElement | HTMLTextAreaElement, start, end);
}

function calculateInputCoordinates(
  el: HTMLInputElement | HTMLTextAreaElement,
  start: number,
  end: number
): { x: number; y: number; width: number; height: number } | null {
  // Approximate layout calculation using computed styles
  const style = window.getComputedStyle(el);
  const text = el.value;
  const paddingLeft = parseFloat(style.paddingLeft) || 0;
  const paddingRight = parseFloat(style.paddingRight) || 0;
  const paddingTop = parseFloat(style.paddingTop) || 0;
  const lineHeight = parseFloat(style.lineHeight) || 20;

  // Approximate line index
  const textBefore = text.slice(0, start);
  const lines = textBefore.split('\n');
  const lineIndex = lines.length - 1;
  const charInLine = lines[lineIndex].length;
  const charWidth = 8; // average character width estimation

  const isRtl = style.direction === 'rtl';
  const y = paddingTop + lineIndex * lineHeight;
  const width = Math.max(10, (end - start) * charWidth);
  const x = isRtl
    ? el.clientWidth - paddingRight - (charInLine * charWidth) - width
    : paddingLeft + (charInLine * charWidth);

  return { x: Math.max(0, x), y, width, height: lineHeight };
}

function calculateContentEditableCoordinates(
  el: HTMLElement,
  start: number,
  end: number
): { x: number; y: number; width: number; height: number } | null {
  try {
    const range = document.createRange();
    let currentOffset = 0;
    let startNode: Node | null = null;
    let startOffset = 0;
    let endNode: Node | null = null;
    let endOffset = 0;

    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let node: Node | null;

    while ((node = walker.nextNode())) {
      const len = node.nodeValue?.length || 0;
      if (!startNode && currentOffset + len >= start) {
        startNode = node;
        startOffset = start - currentOffset;
      }
      if (!endNode && currentOffset + len >= end) {
        endNode = node;
        endOffset = end - currentOffset;
        break;
      }
      currentOffset += len;
    }

    if (startNode && endNode) {
      range.setStart(startNode, Math.min(startOffset, startNode.nodeValue?.length || 0));
      range.setEnd(endNode, Math.min(endOffset, endNode.nodeValue?.length || 0));

      const rect = range.getBoundingClientRect();
      const parentRect = el.getBoundingClientRect();

      return {
        x: rect.left - parentRect.left,
        y: rect.top - parentRect.top,
        width: rect.width,
        height: rect.height,
      };
    }
  } catch {
    // Range calculation error fallback
  }

  return null;
}

let tooltipHideTimer: ReturnType<typeof setTimeout> | null = null;

function showTooltip(e: MouseEvent, issue: Issue, el: HTMLElement) {
  if (tooltipHideTimer) clearTimeout(tooltipHideTimer);

  if (!tooltipElement) {
    tooltipElement = document.createElement('div');
    tooltipElement.className = 'farsi-lint-tooltip';
    document.body.appendChild(tooltipElement);
  }

  tooltipElement.innerHTML = `
    <div class="farsi-lint-tooltip-header">
      <span>${issue.category}</span>
      <span>${issue.severity === 'error' ? 'خطا' : issue.severity === 'warning' ? 'هشدار' : 'پیشنهاد'}</span>
    </div>
    <div class="farsi-lint-tooltip-replacement">
      <span style="text-decoration: line-through; opacity: 0.6;">${issue.original || '(فاصله)'}</span>
      <span>←</span>
      <span style="color: #60a5fa;">${issue.suggestion || '(حذف)'}</span>
    </div>
    <div style="font-size: 12px; margin-bottom: 8px; color: #cbd5e1;">${issue.explanation}</div>
    <button class="farsi-lint-tooltip-btn" id="farsi-lint-apply-btn">اعمال اصلاح</button>
  `;

  tooltipElement.style.left = `${Math.min(window.innerWidth - 300, e.clientX - 100)}px`;
  tooltipElement.style.top = `${e.clientY + 14}px`;
  tooltipElement.style.display = 'block';

  const applyBtn = tooltipElement.querySelector('#farsi-lint-apply-btn');
  if (applyBtn) {
    applyBtn.addEventListener('click', (ev) => {
      ev.preventDefault();
      applyFixToElement(el, issue);
      hideTooltip();
    });
  }
}

function scheduleHideTooltip() {
  tooltipHideTimer = setTimeout(() => {
    hideTooltip();
  }, 300);
}

function hideTooltip() {
  if (tooltipElement) {
    tooltipElement.style.display = 'none';
  }
}

/**
 * Applies a fix back into the page:
 * Supports textarea, input, contenteditable, Gmail compose, LinkedIn/X post boxes.
 * Uses document.execCommand('insertText') / selection replacement to preserve undo history and React state.
 */
export function applyFixToElement(el: HTMLElement, issue: Issue) {
  el.focus();

  if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
    const input = el as HTMLInputElement | HTMLTextAreaElement;
    input.setSelectionRange(issue.start, issue.end);

    // Try execCommand first to preserve undo stack
    const inserted = document.execCommand('insertText', false, issue.suggestion);
    if (!inserted) {
      // Fallback: manually splice value and fire input events
      const val = input.value;
      input.value = val.slice(0, issue.start) + issue.suggestion + val.slice(issue.end);
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
  } else if (el.isContentEditable) {
    try {
      const sel = window.getSelection();
      if (!sel) return;

      const range = document.createRange();
      let currentOffset = 0;
      let startNode: Node | null = null;
      let startOffset = 0;
      let endNode: Node | null = null;
      let endOffset = 0;

      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      let node: Node | null;

      while ((node = walker.nextNode())) {
        const len = node.nodeValue?.length || 0;
        if (!startNode && currentOffset + len >= issue.start) {
          startNode = node;
          startOffset = issue.start - currentOffset;
        }
        if (!endNode && currentOffset + len >= issue.end) {
          endNode = node;
          endOffset = issue.end - currentOffset;
          break;
        }
        currentOffset += len;
      }

      if (startNode && endNode) {
        range.setStart(startNode, startOffset);
        range.setEnd(endNode, endOffset);
        sel.removeAllRanges();
        sel.addRange(range);

        document.execCommand('insertText', false, issue.suggestion);
      }
    } catch {
      // ContentEditable insert error fallback
    }
  }

  // Re-run normalizer to refresh underlines
  setTimeout(() => checkTextAndRun(el), 50);
}

// Auto-run if loaded as content script
if (typeof window !== 'undefined' && typeof document !== 'undefined') {
  initContentScript();
}

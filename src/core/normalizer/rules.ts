/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Issue, NormalizerOptions, Span } from '../../shared/types.ts';
import { findProtectedSpans, isSpanProtected } from './protectedSpans.ts';

const ZWNJ = '\u200c';

export type RuleFunction = (
  text: string,
  options: NormalizerOptions,
  protectedSpans: Span[]
) => Issue[];

/**
 * Rule 1: Arabic ي and ك to Persian ی and ک
 */
export const arabicCharsRule: RuleFunction = (text, _options, protectedSpans) => {
  const issues: Issue[] = [];
  // Arabic Yeh (\u064A) -> Persian Yeh (\u06CC)
  // Arabic Kaf (\u0643) -> Persian Kaf (\u06A9)
  // Arabic Alef Maksura (\u0649) -> Persian Yeh (\u06CC)
  const regex = /[\u064A\u0643\u0649]/g;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;
    if (isSpanProtected(start, end, protectedSpans)) continue;

    const char = match[0];
    let suggestion = '';
    let explanation = '';

    if (char === '\u064A' || char === '\u0649') {
      suggestion = 'ی';
      explanation = 'تبدیل «ي» عربی به «ی» فارسی';
    } else if (char === '\u0643') {
      suggestion = 'ک';
      explanation = 'تبدیل «ك» عربی به «ک» فارسی';
    }

    issues.push({
      id: `arabic-chars-${start}`,
      layer: 'local',
      ruleId: 'arabic-chars',
      category: 'رسم‌الخط (حروف)',
      severity: 'warning',
      start,
      end,
      original: char,
      suggestion,
      explanation,
    });
  }

  return issues;
};

/**
 * Rule 2: Arabic-Indic and English digits to Persian digits
 * Only converted when outside protected spans (code, URLs, emails, Latin words, version numbers).
 */
export const persianDigitsRule: RuleFunction = (text, _options, protectedSpans) => {
  const issues: Issue[] = [];
  // Arabic-Indic: ٠١٢٣٤٥٦٧٨٩ (\u0660-\u0669)
  // ASCII Latin digits: 0-9 (\u0030-\u0039)
  const arabicIndicMap: Record<string, string> = {
    '٠': '۰', '١': '۱', '٢': '۲', '٣': '۳', '٤': '۴',
    '٥': '۵', '٦': '۶', '٧': '۷', '٨': '۸', '٩': '۹',
  };
  const latinMap: Record<string, string> = {
    '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
    '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹',
  };

  // Match consecutive runs of digits
  const regex = /[\u0660-\u06690-9]+/g;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    // Must not be inside protected spans
    if (isSpanProtected(start, end, protectedSpans)) continue;

    const original = match[0];
    let converted = '';
    let hasChange = false;

    for (const ch of original) {
      if (arabicIndicMap[ch]) {
        converted += arabicIndicMap[ch];
        hasChange = true;
      } else if (latinMap[ch]) {
        converted += latinMap[ch];
        hasChange = true;
      } else {
        converted += ch;
      }
    }

    if (hasChange) {
      issues.push({
        id: `persian-digits-${start}`,
        layer: 'local',
        ruleId: 'persian-digits',
        category: 'اعداد فارسی',
        severity: 'suggestion',
        start,
        end,
        original,
        suggestion: converted,
        explanation: 'تبدیل ارقام انگلیسی یا عربی به ارقام فارسی در متن فارسی',
      });
    }
  }

  return issues;
};

/**
 * Rule 3: ZWNJ insertion for prefixes and suffixes
 * Prefixes: می/نمی
 * Suffixes: ها/های, تر/ترین, ام/ای/ایم/اید/اند after ه, etc.
 * Avoids false positives on words like میز, میوه, هایل, هایکو, ترس.
 */
export const zwnjAffixesRule: RuleFunction = (text, _options, protectedSpans) => {
  const issues: Issue[] = [];

  // A. Prefix: می / نمی followed by space + Persian verb stem
  // e.g. "می روم" -> "می‌روم", "نمی دانم" -> "نمی‌دانم"
  // Negative lookahead avoids isolated "می و" or non-verb tokens
  const prefixRegex = /(?:^|[^\u0600-\u06FF\u200c])(ن?می) +([\u0600-\u06FF]+)/g;
  let match: RegExpExecArray | null;

  while ((match = prefixRegex.exec(text)) !== null) {
    const prefix = match[1]; // می or نمی
    const stem = match[2];

    // Don't join if stem is single conjunction like "و" or punctuation
    if (stem === 'و') continue;

    // Calculate start offset of prefix within match[0]
    const prefixOffsetInMatch = match[0].indexOf(prefix);
    const start = match.index + prefixOffsetInMatch;
    const end = start + prefix.length + (match[0].slice(prefixOffsetInMatch + prefix.length).indexOf(stem)) + stem.length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    const fullOriginal = text.slice(start, end);
    const expected = `${prefix}${ZWNJ}${stem}`;

    if (fullOriginal !== expected) {
      issues.push({
        id: `zwnj-prefix-${start}`,
        layer: 'local',
        ruleId: 'zwnj-affixes',
        category: 'نیم‌فاصله (پیشوند)',
        severity: 'error',
        start,
        end,
        original: fullOriginal,
        suggestion: expected,
        explanation: `قرار دادن نیم‌فاصله پس از پیشوند «${prefix}»`,
      });
    }
  }

  // B. Suffixes: ها / های / هایم / هایت / هایش / هایمان / هایتان / هایشان
  // Must be preceded by space after a Persian word
  // Must NOT be followed by Persian letters (e.g. هایل, هایکو, هایده must NOT match!)
  const pluralRegex = /([\u0600-\u06FF]+) +(ها|های|هایم|هایت|هایش|هایمان|هایتان|هایشان)(?=[^\u0600-\u06FF\u200c]|$)/g;
  while ((match = pluralRegex.exec(text)) !== null) {
    const word = match[1];
    const suffix = match[2];

    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    const fullOriginal = match[0];
    const expected = `${word}${ZWNJ}${suffix}`;

    if (fullOriginal !== expected) {
      issues.push({
        id: `zwnj-plural-${start}`,
        layer: 'local',
        ruleId: 'zwnj-affixes',
        category: 'نیم‌فاصله (نشانه جمع)',
        severity: 'error',
        start,
        end,
        original: fullOriginal,
        suggestion: expected,
        explanation: `قرار دادن نیم‌فاصله قبل از نشانه جمع «${suffix}»`,
      });
    }
  }

  // C. Suffixes: تر / ترین
  // Preceded by Persian word + space
  // Must NOT be followed by Persian letters (e.g. ترسناک, تربت must not match)
  const compRegex = /([\u0600-\u06FF]+) +(تر|ترین)(?=[^\u0600-\u06FF\u200c]|$)/g;
  while ((match = compRegex.exec(text)) !== null) {
    const word = match[1];
    const suffix = match[2];

    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    const fullOriginal = match[0];
    const expected = `${word}${ZWNJ}${suffix}`;

    if (fullOriginal !== expected) {
      issues.push({
        id: `zwnj-comp-${start}`,
        layer: 'local',
        ruleId: 'zwnj-affixes',
        category: 'نیم‌فاصله (صفت تفضیلی/عالی)',
        severity: 'error',
        start,
        end,
        original: fullOriginal,
        suggestion: expected,
        explanation: `قرار دادن نیم‌فاصله قبل از «${suffix}»`,
      });
    }
  }

  // D. Verbal & Indefinite suffixes after silent heh (ه / هٔ):
  // ام / ای / ایم / اید / اند
  // e.g. "رفته ام" -> "رفته‌ام", "خانه ای" -> "خانه‌ای"
  const hehSuffixRegex = /([\u0600-\u06FF]*[هۀ]) +(ام|ای|ایم|اید|اند)(?=[^\u0600-\u06FF\u200c]|$)/g;
  while ((match = hehSuffixRegex.exec(text)) !== null) {
    const word = match[1];
    const suffix = match[2];

    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    const fullOriginal = match[0];
    const expected = `${word}${ZWNJ}${suffix}`;

    if (fullOriginal !== expected) {
      issues.push({
        id: `zwnj-heh-suffix-${start}`,
        layer: 'local',
        ruleId: 'zwnj-affixes',
        category: 'نیم‌فاصله (پسوندهای پس از ه)',
        severity: 'error',
        start,
        end,
        original: fullOriginal,
        suggestion: expected,
        explanation: `قرار دادن نیم‌فاصله پس از «ه» بیان حرکت قبل از «${suffix}»`,
      });
    }
  }

  return issues;
};

/**
 * Rule 4: Removal of redundant ZWNJ next to spaces; collapsing multiple spaces
 */
export const cleanZwnjAndSpacesRule: RuleFunction = (text, _options, protectedSpans) => {
  const issues: Issue[] = [];

  // A. Redundant ZWNJ adjacent to regular space or whitespace:
  // e.g. " \u200c ", "\u200c ", " \u200c"
  const zwnjSpaceRegex = /(?:[ ]+\u200c|\u200c[ ]+)+/g;
  let match: RegExpExecArray | null;

  while ((match = zwnjSpaceRegex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    issues.push({
      id: `clean-zwnj-space-${start}`,
      layer: 'local',
      ruleId: 'clean-zwnj-spaces',
      category: 'فاصله‌گذاری',
      severity: 'warning',
      start,
      end,
      original: match[0],
      suggestion: ' ',
      explanation: 'حذف نیم‌فاصله زائد در کنار فاصله معمولی',
    });
  }

  // B. Multiple consecutive ZWNJs: \u200c\u200c+
  const multiZwnjRegex = /\u200c{2,}/g;
  while ((match = multiZwnjRegex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    issues.push({
      id: `multi-zwnj-${start}`,
      layer: 'local',
      ruleId: 'clean-zwnj-spaces',
      category: 'فاصله‌گذاری',
      severity: 'suggestion',
      start,
      end,
      original: match[0],
      suggestion: ZWNJ,
      explanation: 'تبدیل چند نیم‌فاصله پیاپی به یک نیم‌فاصله',
    });
  }

  // C. Multiple consecutive horizontal spaces (excluding newlines): e.g. "   " -> " "
  const multiSpaceRegex = /[ ]{2,}/g;
  while ((match = multiSpaceRegex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    issues.push({
      id: `multi-space-${start}`,
      layer: 'local',
      ruleId: 'clean-zwnj-spaces',
      category: 'فاصله‌گذاری',
      severity: 'suggestion',
      start,
      end,
      original: match[0],
      suggestion: ' ',
      explanation: 'تبدیل چند فاصله متوالی به یک فاصله',
    });
  }

  return issues;
};

/**
 * Rule 5: Persian punctuation marks (، ؛ ؟) and correct spacing around punctuation
 * No space before punctuation, one space after punctuation when followed by words.
 */
export const punctuationMarksRule: RuleFunction = (text, _options, protectedSpans) => {
  const issues: Issue[] = [];

  // A. English punctuation to Persian punctuation: , ; ?
  // Avoid converting commas/semicolons inside protected spans or code
  const engPunctRegex = /[,;?]/g;
  let match: RegExpExecArray | null;

  while ((match = engPunctRegex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    const char = match[0];
    let suggestion = '';
    let explanation = '';

    if (char === ',') {
      suggestion = '،';
      explanation = 'تبدیل ویرگول انگلیسی به ویرگول فارسی (،)';
    } else if (char === ';') {
      suggestion = '؛';
      explanation = 'تبدیل نقطه-ویرگول انگلیسی به فارسی (؛)';
    } else if (char === '?') {
      suggestion = '؟';
      explanation = 'تبدیل علامت سؤال انگلیسی به فارسی (؟)';
    }

    issues.push({
      id: `punct-conv-${start}`,
      layer: 'local',
      ruleId: 'punctuation-marks',
      category: 'نشانه‌گذاری',
      severity: 'warning',
      start,
      end,
      original: char,
      suggestion,
      explanation,
    });
  }

  // B. Spacing around punctuation:
  // e.g. "کلمه ، کلمه" -> "کلمه، کلمه" (space before punctuation should be removed)
  // or "کلمه،کلمه" -> "کلمه، کلمه" (missing space after punctuation)
  const punctSpacingRegex = /([ ]+)?([،؛؟!:])([ ]+)?/g;
  while ((match = punctSpacingRegex.exec(text)) !== null) {
    const spaceBefore = match[1] || '';
    const punct = match[2];
    const spaceAfter = match[3] || '';
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    // Check if followed by newline, end of string, closing quote/bracket, or digits (e.g. 12:30)
    const nextChar = text[end] || '';
    const prevChar = text[start - 1] || '';

    // Ignore time format like 12:30
    if (punct === ':' && /\d/.test(prevChar) && /\d/.test(nextChar)) {
      continue;
    }

    // If there is space before punctuation
    if (spaceBefore.length > 0) {
      issues.push({
        id: `punct-space-before-${start}`,
        layer: 'local',
        ruleId: 'punctuation-marks',
        category: 'فاصله‌گذاری نشانه‌ها',
        severity: 'warning',
        start,
        end: start + spaceBefore.length,
        original: spaceBefore,
        suggestion: '',
        explanation: `حذف فاصله زائد پیش از نشانه «${punct}»`,
      });
    }

    // If there is NO space after punctuation, but followed by a Persian/Latin word
    if (spaceAfter.length === 0 && /[\u0600-\u06FFA-Za-z]/.test(nextChar)) {
      issues.push({
        id: `punct-space-after-${end}`,
        layer: 'local',
        ruleId: 'punctuation-marks',
        category: 'فاصله‌گذاری نشانه‌ها',
        severity: 'warning',
        start: end,
        end,
        original: '',
        suggestion: ' ',
        explanation: `افزودن فاصله پس از نشانه «${punct}»`,
      });
    }
  }

  return issues;
};

/**
 * Rule 6: English quotes to «» and spacing around () [] «»
 */
export const quotesAndBracketsRule: RuleFunction = (text, _options, protectedSpans) => {
  const issues: Issue[] = [];

  // A. English double quotes "text" -> «text»
  // Smart pair matching
  const quotePairRegex = /"([^"\n]+)"/g;
  let match: RegExpExecArray | null;

  while ((match = quotePairRegex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    const inner = match[1].trim();
    issues.push({
      id: `quotes-pair-${start}`,
      layer: 'local',
      ruleId: 'quotes-brackets',
      category: 'گیومه فارسی',
      severity: 'suggestion',
      start,
      end,
      original: match[0],
      suggestion: `«${inner}»`,
      explanation: 'تبدیل علامت نقل‌قول انگلیسی (" ") به گیومه فارسی (« »)',
    });
  }

  // B. Spacing inside brackets: ( text ) -> (text), [ text ] -> [text], « text » -> «text»
  const insideBracketRegex = /(\([ ]+)|([ ]+\))|(\[[ ]+)|([ ]+\])|(«[ ]+)|([ ]+»)/g;
  while ((match = insideBracketRegex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    const char = match[0].trim();
    issues.push({
      id: `bracket-inner-space-${start}`,
      layer: 'local',
      ruleId: 'quotes-brackets',
      category: 'فاصله‌گذاری کمانک',
      severity: 'warning',
      start,
      end,
      original: match[0],
      suggestion: char,
      explanation: `حذف فاصله زائد داخل «${char}»`,
    });
  }

  return issues;
};

/**
 * Rule 7: ... to … (ellipsis) and remove kashida (ـ \u0640)
 */
export const kashidaAndEllipsisRule: RuleFunction = (text, _options, protectedSpans) => {
  const issues: Issue[] = [];

  // A. Three or more dots: ... -> … (\u2026)
  const dotsRegex = /\.{3,}/g;
  let match: RegExpExecArray | null;

  while ((match = dotsRegex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    issues.push({
      id: `ellipsis-${start}`,
      layer: 'local',
      ruleId: 'kashida-ellipsis',
      category: 'سه‌نقطه',
      severity: 'suggestion',
      start,
      end,
      original: match[0],
      suggestion: '…',
      explanation: 'تبدیل سه‌نقطه پی‌درپی (...) به نشانه استاندارد سه‌نقطه (…)',
    });
  }

  // B. Kashida (ـ \u0640 tatweel)
  const kashidaRegex = /\u0640+/g;
  while ((match = kashidaRegex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    issues.push({
      id: `kashida-${start}`,
      layer: 'local',
      ruleId: 'kashida-ellipsis',
      category: 'کشیده (تطویل)',
      severity: 'warning',
      start,
      end,
      original: match[0],
      suggestion: '',
      explanation: 'حذف کشیدگی زائد حروف (کشیده/تطویل)',
    });
  }

  return issues;
};

/**
 * Rule 8: "ه ی" -> "هٔ" or "هی" (configurable ezafe style)
 * e.g. "خانه ی من" -> "خانهٔ من" or "خانه‌ی من"
 */
export const ezafeStyleRule: RuleFunction = (text, options, protectedSpans) => {
  const issues: Issue[] = [];
  const regex = /([\u0600-\u06FF]*[هۀ]) +[یی]\b/g;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;

    if (isSpanProtected(start, end, protectedSpans)) continue;

    const base = match[1];
    const suggestion = options.ezafeStyle === 'hamza'
      ? `${base.replace(/ۀ$/, 'ه')}ٔ`
      : `${base.replace(/ۀ$/, 'ه')}${ZWNJ}ی`;

    issues.push({
      id: `ezafe-style-${start}`,
      layer: 'local',
      ruleId: 'ezafe-style',
      category: 'اضافه بعد از ه',
      severity: 'warning',
      start,
      end,
      original: match[0],
      suggestion,
      explanation: options.ezafeStyle === 'hamza'
        ? 'اصلاح نشانه اضافه پس از «ه» به صورت همزه (هٔ)'
        : 'اصلاح نشانه اضافه پس از «ه» به صورت «هی» با نیم‌فاصله',
    });
  }

  return issues;
};

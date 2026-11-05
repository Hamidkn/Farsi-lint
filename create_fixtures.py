#!/usr/bin/env python3
"""
create_fixtures.py — Generates the entire fixtures/ directory for the farsi-lint project.
Idempotent generator creating schemas, normalizer cases, clean docs, and AI evaluation samples.
"""

import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = REPO_ROOT / "fixtures"

ZWNJ = "\u200c"


def write_file(path: Path, content: str) -> None:
    """Writes a text file with UTF-8 encoding and standard unix newlines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def dump_json_with_zwnj_escapes(obj) -> str:
    """
    Serializes obj to formatted JSON and converts literal U+200C characters
    into explicit 6-character '\\u200c' escape sequences so they stay visible
    to human reviewers in editors and diff viewers.
    """
    raw = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    return raw.replace("\u200c", "\\u200c")


# ==============================================================================
# 1. JSON Schemas (schema/)
# ==============================================================================

NORMALIZER_CASES_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "NormalizerCases",
    "description": "Schema for rule-based Persian normalizer test fixtures",
    "type": "object",
    "required": ["rule", "description_en", "cases"],
    "properties": {
        "rule": {"type": "string"},
        "description_en": {"type": "string"},
        "cases": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "id",
                    "input",
                    "expected",
                    "options",
                    "kind",
                    "note",
                    "reviewed",
                ],
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-z-]+-\\d{3}$"},
                    "input": {"type": "string"},
                    "expected": {"type": "string"},
                    "options": {"type": "object"},
                    "kind": {"type": "string", "enum": ["positive", "negative"]},
                    "note": {"type": "string"},
                    "reviewed": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}

AI_SAMPLE_EXPECTED_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AISampleExpected",
    "description": "Schema for expected issues in AI-generated Persian evaluation samples",
    "type": "object",
    "required": ["sample", "source", "issues", "reviewed"],
    "properties": {
        "sample": {"type": "string"},
        "source": {"type": "string"},
        "reviewed": {"type": "boolean"},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "quote",
                    "category",
                    "severity",
                    "suggestion",
                    "explanation_fa",
                    "must_detect",
                ],
                "properties": {
                    "quote": {"type": "string", "minLength": 1},
                    "category": {
                        "type": "string",
                        "enum": [
                            "translationese",
                            "unnatural",
                            "grammar",
                            "register",
                            "collocation",
                            "redundancy",
                            "terminology",
                            "clarity",
                        ],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["error", "warning", "suggestion"],
                    },
                    "suggestion": {"type": "string"},
                    "explanation_fa": {"type": "string"},
                    "must_detect": {"type": "boolean"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}

# ==============================================================================
# 2. README Files
# ==============================================================================

CLEAN_README_MD = """# Clean Persian Text Corpus / پیکره متون پاکیزه فارسی

## English Instructions
This directory is reserved exclusively for human-written, professionally edited Persian texts.
**Under no circumstances should AI-generated or machine-translated text be placed in this folder.**

### Purpose and Rules
- Every file placed here serves as a zero-false-positive benchmark: the local normalizer layer must produce **zero issues** on all files in this directory.
- Suggested sources:
  1. Carefully self-authored and proofread texts by project maintainers.
  2. Featured or good articles (مقاله‌های برگزیده و خوب) from Persian Wikipedia under the CC BY-SA 4.0 license.
- When adding text from external sources:
  - Verify every single ZWNJ, punctuation mark, and spacing rule by hand.
  - Record full source attribution, URL, and license in `fixtures/README.md`.
- File naming convention:
  `NN-source-topic.txt` (e.g. `01-fa-wiki-hafez.txt`, `02-dehkhoda-prose.txt`).
- Format: UTF-8 encoding, LF newlines, one or more paragraphs.

---

## راهنمای فارسی
این پوشه منحصراً به متون اصیل فارسی، نگارش‌شده و ویرایش‌شده توسط ویراستاران حرفه‌ای و انسان اختصاص دارد.
**به هیچ عنوان نباید متون تولیدشده توسط هوش مصنوعی یا ترجمه‌های ماشینی در این بخش قرار گیرند.**

### اهداف و ضوابط
- تمامی متون این پوشه برای سنجش خطای کاذب (False Positive) لایه محلی به کار می‌روند؛ بنابراین اجرای نرمالایزر روی این فایل‌ها باید دقیقاً **صفر ایراد** گزارش کند.
- منابع پیشنهادی:
  ۱. یادداشت‌ها و مقالات ویرایش‌شده با دقت بالا توسط توسعه‌دهندگان و ویراستاران پروژه.
  ۲. مقاله‌های برگزیده یا خوب ویکی‌پدیای فارسی تحت مجوز CC BY-SA 4.0.
- ضوابط افزودن متن جدید:
  - نیم‌فاصله‌ها، ارقام، نشانه‌گذاری‌ها و حروف باید سطر‌به‌سطر توسط انسان بازبینی گردند.
  - منبع دقیق، پیوند اینترنتی و مجوز در جدول `fixtures/README.md` ثبت شود.
- شیوه نام‌گذاری:
  `NN-source-topic.txt` (مانند `01-fa-wiki-hafez.txt`).
- قالب پرونده‌ها: یونیکد (UTF-8) با انتهای خط یونیکس (LF).
"""

FIXTURES_README_MD = """# Farsi-lint Test Fixtures / داده‌های آزمون فارسی‌لینت

## Overview / معرفی
This directory contains the ground-truth test fixtures for `farsi-lint`.
این پوشه شامل داده‌های معیار و آزمون‌های مبنای پروژه فارسی‌لینت است.

## Folder Structure / ساختار پوشه‌ها
- `schema/`: JSON Schema definitions (Draft 2020-12) defining the structural format for normalizer test cases and AI sample evaluations.
- `clean/`: High-quality human-written Persian reference texts used to enforce a 0% false-positive rate on professionally published Persian prose. Contains instructions only; no synthetic text.
- `normalizer/`: Unit test fixtures for each individual rule of the local rule-based layer (orthography, ZWNJ, digits, punctuation, kashida, protected spans, and combined multi-rule cases).
- `ai-samples/`: Synthetic evaluation pairs (`.txt` input paired with `.expected.json` ground truth) testing the LLM review layer against typical AI translation and phrasing pitfalls.

## Ground Truth Invariance Rule
> **Important:** Fixture files represent the canonical editorial ground truth. They must NEVER be altered, relaxed, or generated with loose assertions merely to make software tests pass. If a test fails against a reviewed fixture, the code or rule configuration is defective, not the fixture.

## Review Workflow / فرایند بازبینی انسانی
1. All generated fixture cases start with `"reviewed": false`.
2. A native Persian speaker / copyeditor manually audits each case, verifying standard orthography based on the Academy of Persian Language and Literature (فرهنگستان زبان و ادب فارسی).
3. Once verified, the reviewer flips `"reviewed": true`.
4. Automated CI test suites load and assert against cases that have been reviewed.

## Representation of ZWNJ (نیم‌فاصله)
- **In `.json` files**: The Zero-Width Non-Joiner (U+200C) is stored explicitly as the 6-character sequence `\\u200c`. This ensures the character is visually explicit in code reviews, pull requests, and terminal outputs.
- **In `.txt` files**: The real, standard UTF-8 binary character U+200C is used directly, matching realistic browser inputs.

## Sources and Licenses / منابع و مجوزها

| File / Folder | Source | License | Attribution |
| :--- | :--- | :--- | :--- |
| `schema/*.json` | synthetic | CC0-1.0 | Farsi-lint Core Team |
| `normalizer/*.json` | synthetic | CC0-1.0 | Farsi-lint Core Team |
| `ai-samples/*.txt` | synthetic | CC0-1.0 | Farsi-lint Core Team (simulating typical LLM translation pitfalls) |
| `ai-samples/*.expected.json` | synthetic | CC0-1.0 | Farsi-lint Core Team |
| `clean/` | human-authored | CC BY-SA 4.0 / CC0 | Documented per-file upon manual addition |
"""

# ==============================================================================
# 3. Normalizer Test Cases (13 Files)
# ==============================================================================


def get_arabic_letters_data():
    return {
        "rule": "arabic-letters",
        "description_en": "Convert Arabic Yeh (ي/ى) and Kaf (ك) to Persian counterparts (ی/ک) while preserving standard Persian hamza spellings.",
        "cases": [
            {
                "id": "arabic-letters-001",
                "input": "علي به مدرسه رفت.",
                "expected": "علی به مدرسه رفت.",
                "options": {},
                "kind": "positive",
                "note": "Arabic Yeh at word end",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-002",
                "input": "كتاب را باز كرد.",
                "expected": "کتاب را باز کرد.",
                "options": {},
                "kind": "positive",
                "note": "Arabic Kaf at word beginning and inside",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-003",
                "input": "تاريك و نمناك بود.",
                "expected": "تاریک و نمناک بود.",
                "options": {},
                "kind": "positive",
                "note": "Arabic Kaf at word end",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-004",
                "input": "پزشكي علمي دقيق است.",
                "expected": "پزشکی علمی دقیق است.",
                "options": {},
                "kind": "positive",
                "note": "Arabic Yeh in medial and final positions",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-005",
                "input": "حركت سريع لاك‌پشت",
                "expected": "حرکت سریع لاک‌پشت",
                "options": {},
                "kind": "positive",
                "note": "Arabic Kaf in common Persian words",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-006",
                "input": "موسي و عيسي",
                "expected": "موسی و عیسی",
                "options": {},
                "kind": "positive",
                "note": "Arabic Alef Maksura to Persian Yeh",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-007",
                "input": "كودك در بانك بود.",
                "expected": "کودک در بانک بود.",
                "options": {},
                "kind": "positive",
                "note": "Multiple Arabic Kaf occurrences",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-008",
                "input": "ديكته و نقاشي",
                "expected": "دیکته و نقاشی",
                "options": {},
                "kind": "positive",
                "note": "Arabic Kaf and Yeh in compound sentence",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-009",
                "input": "يك برگ خشك",
                "expected": "یک برگ خشک",
                "options": {},
                "kind": "positive",
                "note": "Arabic Kaf at beginning and end",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-010",
                "input": "بزرگي و شكوه",
                "expected": "بزرگی و شکوه",
                "options": {},
                "kind": "positive",
                "note": "Arabic Yeh and Kaf in coordinated nouns",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-011",
                "input": "مسئله حل شد.",
                "expected": "مسئله حل شد.",
                "options": {},
                "kind": "negative",
                "note": "Standard Persian spelling of مسئله must not be modified",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-012",
                "input": "مسأله حل شد.",
                "expected": "مسأله حل شد.",
                "options": {},
                "kind": "negative",
                "note": "Alternative accepted Persian spelling مسأله must remain untouched",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-013",
                "input": "رئیس اداره آمد.",
                "expected": "رئیس اداره آمد.",
                "options": {},
                "kind": "negative",
                "note": "Persian hamza in رئیس must remain untouched",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-014",
                "input": "تأثیر مثبت بر جامعه",
                "expected": "تأثیر مثبت بر جامعه",
                "options": {},
                "kind": "negative",
                "note": "Persian alef hamza in تأثیر must remain untouched",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-015",
                "input": "مؤلف کتاب حاضر",
                "expected": "مؤلف کتاب حاضر",
                "options": {},
                "kind": "negative",
                "note": "Persian waw hamza in مؤلف must remain untouched",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-016",
                "input": "دایره‌المعارف بزرگ اسلامی",
                "expected": "دایره‌المعارف بزرگ اسلامی",
                "options": {},
                "kind": "negative",
                "note": "Correct Persian loanword with ayn and ezafe",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-017",
                "input": "کتاب و دفتر من روی میز است.",
                "expected": "کتاب و دفتر من روی میز است.",
                "options": {},
                "kind": "negative",
                "note": "Already correct Persian kaf and yeh",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-018",
                "input": "خیابان‌های تمیز و چراغ‌های روشن",
                "expected": "خیابان‌های تمیز و چراغ‌های روشن",
                "options": {},
                "kind": "negative",
                "note": "Already clean Persian text with proper letters",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-019",
                "input": "پژوهشگاه فرهنگ و اندیشه اسلامی",
                "expected": "پژوهشگاه فرهنگ و اندیشه اسلامی",
                "options": {},
                "kind": "negative",
                "note": "Proper Persian institution name already correct",
                "reviewed": False,
            },
            {
                "id": "arabic-letters-020",
                "input": "هیئت مدیره تشکیل جلسه داد.",
                "expected": "هیئت مدیره تشکیل جلسه داد.",
                "options": {},
                "kind": "negative",
                "note": "Accepted Persian spelling of هیئت must not change",
                "reviewed": False,
            },
        ],
    }


def get_digits_data():
    return {
        "rule": "digits",
        "description_en": "Convert Arabic-Indic and ASCII digits to Persian digits when configured, protecting digits in code, URLs, version numbers, and Latin words.",
        "cases": [
            {
                "id": "digits-001",
                "input": "در سال 1403 فارغ‌التحصیل شد.",
                "expected": "در سال ۱۴۰۳ فارغ‌التحصیل شد.",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Convert 4-digit English year to Persian digits",
                "reviewed": False,
            },
            {
                "id": "digits-002",
                "input": "تعداد 25 نفر شرکت کردند.",
                "expected": "تعداد ۲۵ نفر شرکت کردند.",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Convert English count to Persian digits",
                "reviewed": False,
            },
            {
                "id": "digits-003",
                "input": "قیمت آن 50000 تومان است.",
                "expected": "قیمت آن ۵۰۰۰۰ تومان است.",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Convert Persian price digits",
                "reviewed": False,
            },
            {
                "id": "digits-004",
                "input": "در روز 12 فروردین ماه",
                "expected": "در روز ۱۲ فروردین ماه",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Calendar day conversion",
                "reviewed": False,
            },
            {
                "id": "digits-005",
                "input": "قیمت ٥٠٠ تومان است.",
                "expected": "قیمت ۵۰۰ تومان است.",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Convert Arabic-Indic digits ٥٠٠ to Persian ۵۰۰",
                "reviewed": False,
            },
            {
                "id": "digits-006",
                "input": "در سال ١٤٠٢ خورشیدی",
                "expected": "در سال ۱۴۰۲ خورشیدی",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Convert Arabic-Indic year to Persian",
                "reviewed": False,
            },
            {
                "id": "digits-007",
                "input": "کد ملی ثبت‌شده ٩٨ است.",
                "expected": "کد ملی ثبت‌شده ۹۸ است.",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Convert Arabic-Indic digits ٩٨",
                "reviewed": False,
            },
            {
                "id": "digits-008",
                "input": "اتاق شماره 7 طبقه 3",
                "expected": "اتاق شماره ۷ طبقه ۳",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Multiple single digits in sentence",
                "reviewed": False,
            },
            {
                "id": "digits-009",
                "input": "صفحه 120 از 350 کتاب",
                "expected": "صفحه ۱۲۰ از ۳۵۰ کتاب",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Page numbers conversion",
                "reviewed": False,
            },
            {
                "id": "digits-010",
                "input": "در سال 1403 هستیم.",
                "expected": "در سال 1403 هستیم.",
                "options": {"digits": "keep"},
                "kind": "negative",
                "note": "Option digits=keep leaves English digits unchanged",
                "reviewed": False,
            },
            {
                "id": "digits-011",
                "input": "فایل صوتی با پسوند MP3 ذخیره شد.",
                "expected": "فایل صوتی با پسوند MP3 ذخیره شد.",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "Digits inside English technical word MP3 must not change",
                "reviewed": False,
            },
            {
                "id": "digits-012",
                "input": "رمزگذاری استاندارد UTF8 است.",
                "expected": "رمزگذاری استاندارد UTF8 است.",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "Digits in UTF8 must not change",
                "reviewed": False,
            },
            {
                "id": "digits-013",
                "input": "نسخه جدید v2.1 منتشر گردید.",
                "expected": "نسخه جدید v2.1 منتشر گردید.",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "Version number v2.1 must not change",
                "reviewed": False,
            },
            {
                "id": "digits-014",
                "input": "برنامه به نگارش 3.5.0 ارتقا یافت.",
                "expected": "برنامه به نگارش 3.5.0 ارتقا یافت.",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "Semantic version number 3.5.0 must not change",
                "reviewed": False,
            },
            {
                "id": "digits-015",
                "input": "آدرس وبگاه https://example.com/item/123 است.",
                "expected": "آدرس وبگاه https://example.com/item/123 است.",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "Digits inside URL must not change",
                "reviewed": False,
            },
            {
                "id": "digits-016",
                "input": "پیام را به info@domain123.com بفرستید.",
                "expected": "پیام را به info@domain123.com بفرستید.",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "Digits inside email address must not change",
                "reviewed": False,
            },
            {
                "id": "digits-017",
                "input": "زمان ثبت گزارش 2024-11-05T08:00:00Z بود.",
                "expected": "زمان ثبت گزارش 2024-11-05T08:00:00Z بود.",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "ISO timestamp in Latin format must remain unchanged",
                "reviewed": False,
            },
            {
                "id": "digits-018",
                "input": "تماس با شماره Call +1-800-555-0199 now فوری",
                "expected": "تماس با شماره Call +1-800-555-0199 now فوری",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "Phone number in Latin context must remain unchanged",
                "reviewed": False,
            },
            {
                "id": "digits-019",
                "input": "دستور const port = 3000; در جاوااسکریپت",
                "expected": "دستور const port = 3000; در جاوااسکریپت",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "Port number in code context must remain unchanged",
                "reviewed": False,
            },
            {
                "id": "digits-020",
                "input": "کتابخانه React19 در دسترس است.",
                "expected": "کتابخانه React19 در دسترس است.",
                "options": {"digits": "persian"},
                "kind": "negative",
                "note": "Alphanumeric technology brand React19 must remain unchanged",
                "reviewed": False,
            },
        ],
    }


def get_zwnj_data():
    return {
        "rule": "zwnj",
        "description_en": "Insert ZWNJ between stems and prefixes/suffixes (می/نمی، ها/های، تر/ترین، پسوندهای بعد از ه) without corrupting standalone words.",
        "cases": [
            {
                "id": "zwnj-001",
                "input": "او به مدرسه می رود.",
                "expected": f"او به مدرسه می{ZWNJ}رود.",
                "options": {},
                "kind": "positive",
                "note": "Prefix می with verb stem",
                "reviewed": False,
            },
            {
                "id": "zwnj-002",
                "input": "من حقیقت را نمی دانم.",
                "expected": f"من حقیقت را نمی{ZWNJ}دانم.",
                "options": {},
                "kind": "positive",
                "note": "Prefix نمی with verb stem",
                "reviewed": False,
            },
            {
                "id": "zwnj-003",
                "input": "کتاب ها روی قفسه چیده شده‌اند.",
                "expected": f"کتاب{ZWNJ}ها روی قفسه چیده شده‌اند.",
                "options": {},
                "kind": "positive",
                "note": "Plural suffix ها",
                "reviewed": False,
            },
            {
                "id": "zwnj-004",
                "input": "پنجره های اتاق باز هستند.",
                "expected": f"پنجره{ZWNJ}های اتاق باز هستند.",
                "options": {},
                "kind": "positive",
                "note": "Plural suffix های",
                "reviewed": False,
            },
            {
                "id": "zwnj-005",
                "input": "روزگاران سختی هایی دارد.",
                "expected": f"روزگاران سختی{ZWNJ}هایی دارد.",
                "options": {},
                "kind": "positive",
                "note": "Indefinite plural suffix هایی",
                "reviewed": False,
            },
            {
                "id": "zwnj-006",
                "input": "این درخت بزرگ تر از آن است.",
                "expected": f"این درخت بزرگ{ZWNJ}تر از آن است.",
                "options": {},
                "kind": "positive",
                "note": "Comparative suffix تر",
                "reviewed": False,
            },
            {
                "id": "zwnj-007",
                "input": "زیبا ترین گل بوستان",
                "expected": f"زیبا{ZWNJ}ترین گل بوستان",
                "options": {},
                "kind": "positive",
                "note": "Superlative suffix ترین",
                "reviewed": False,
            },
            {
                "id": "zwnj-008",
                "input": "بسیار خسته ام و نیاز به استراحت دارم.",
                "expected": f"بسیار خسته{ZWNJ}ام و نیاز به استراحت دارم.",
                "options": {},
                "kind": "positive",
                "note": "Suffix ام after silent heh",
                "reviewed": False,
            },
            {
                "id": "zwnj-009",
                "input": "آیا آن منظره را دیده ای؟",
                "expected": f"آیا آن منظره را دیده{ZWNJ}ای؟",
                "options": {},
                "kind": "positive",
                "note": "Suffix ای after silent heh",
                "reviewed": False,
            },
            {
                "id": "zwnj-010",
                "input": "به خانه ای دوردست رفتیم.",
                "expected": f"به خانه{ZWNJ}ای دوردست رفتیم.",
                "options": {},
                "kind": "positive",
                "note": "Indefinite noun suffix ای after silent heh",
                "reviewed": False,
            },
            {
                "id": "zwnj-011",
                "input": "آنها به شهر رسیده اند.",
                "expected": f"آنها به شهر رسیده{ZWNJ}اند.",
                "options": {},
                "kind": "positive",
                "note": "Suffix اند after silent heh",
                "reviewed": False,
            },
            {
                "id": "zwnj-012",
                "input": "میز کار چوبی بسیار تمیز است.",
                "expected": "میز کار چوبی بسیار تمیز است.",
                "options": {},
                "kind": "negative",
                "note": "Word میز must not be split with ZWNJ",
                "reviewed": False,
            },
            {
                "id": "zwnj-013",
                "input": "میوه تازه در سبد چیده شد.",
                "expected": "میوه تازه در سبد چیده شد.",
                "options": {},
                "kind": "negative",
                "note": "Word میوه must not be split with ZWNJ",
                "reviewed": False,
            },
            {
                "id": "zwnj-014",
                "input": "میهن دوستی از ویژگی‌های ارزنده است.",
                "expected": "میهن دوستی از ویژگی‌های ارزنده است.",
                "options": {},
                "kind": "negative",
                "note": "Word میهن must not be split with ZWNJ",
                "reviewed": False,
            },
            {
                "id": "zwnj-015",
                "input": "دانه درشت هایل بر زمین بارید.",
                "expected": "دانه درشت هایل بر زمین بارید.",
                "options": {},
                "kind": "negative",
                "note": "Root word هایل must not be treated as plural suffix",
                "reviewed": False,
            },
            {
                "id": "zwnj-016",
                "input": "ترانه دلنشین به گوش می‌رسید.",
                "expected": "ترانه دلنشین به گوش می‌رسید.",
                "options": {},
                "kind": "negative",
                "note": "Word ترانه starting with تر must not be split",
                "reviewed": False,
            },
            {
                "id": "zwnj-017",
                "input": "بستر نرم و راحت رودخانه",
                "expected": "بستر نرم و راحت رودخانه",
                "options": {},
                "kind": "negative",
                "note": "Word بستر ending with تر must not be split",
                "reviewed": False,
            },
            {
                "id": "zwnj-018",
                "input": "تناسب اندام اهمیت فراوانی دارد.",
                "expected": "تناسب اندام اهمیت فراوانی دارد.",
                "options": {},
                "kind": "negative",
                "note": "Word اندام must not be split with ZWNJ",
                "reviewed": False,
            },
            {
                "id": "zwnj-019",
                "input": "ماهی قرمز در آب شنا می‌کند.",
                "expected": "ماهی قرمز در آب شنا می‌کند.",
                "options": {},
                "kind": "negative",
                "note": "Word ماهی must not be treated as heh+ye",
                "reviewed": False,
            },
            {
                "id": "zwnj-020",
                "input": "کتابی ارزشمند درباره تاریخ ایران",
                "expected": "کتابی ارزشمند درباره تاریخ ایران",
                "options": {},
                "kind": "negative",
                "note": "Word کتابی with standard ya must not receive ZWNJ",
                "reviewed": False,
            },
        ],
    }


def get_zwnj_cleanup_data():
    return {
        "rule": "zwnj-cleanup",
        "description_en": "Remove redundant ZWNJ next to space, duplicate ZWNJs, and ZWNJ at word boundaries or after non-joining letters.",
        "cases": [
            {
                "id": "zwnj-cleanup-001",
                "input": f"کتاب {ZWNJ} من",
                "expected": "کتاب من",
                "options": {},
                "kind": "positive",
                "note": "ZWNJ directly preceded by space",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-002",
                "input": f"کتاب{ZWNJ} من",
                "expected": "کتاب من",
                "options": {},
                "kind": "positive",
                "note": "ZWNJ directly followed by space",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-003",
                "input": f"می{ZWNJ}{ZWNJ}روم",
                "expected": f"می{ZWNJ}روم",
                "options": {},
                "kind": "positive",
                "note": "Duplicate consecutive ZWNJs collapsed to one",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-004",
                "input": f"{ZWNJ}سلام دنیا",
                "expected": "سلام دنیا",
                "options": {},
                "kind": "positive",
                "note": "ZWNJ at the start of sentence",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-005",
                "input": f"پایان متن{ZWNJ}",
                "expected": "پایان متن",
                "options": {},
                "kind": "positive",
                "note": "ZWNJ at the end of sentence",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-006",
                "input": f"روز{ZWNJ}به",
                "expected": "روزبه",
                "options": {},
                "kind": "positive",
                "note": "Redundant ZWNJ after non-joining letter 'ز'",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-007",
                "input": f"رود{ZWNJ}خانه",
                "expected": "رودخانه",
                "options": {},
                "kind": "positive",
                "note": "Redundant ZWNJ after non-joining letter 'د'",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-008",
                "input": f"باز{ZWNJ}گشت",
                "expected": "بازگشت",
                "options": {},
                "kind": "positive",
                "note": "Redundant ZWNJ after non-joining letter 'ز' in simple compound",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-009",
                "input": f"دروازه{ZWNJ} ها",
                "expected": "دروازه ها",
                "options": {},
                "kind": "positive",
                "note": "ZWNJ adjacent to space before plural suffix",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-010",
                "input": f"می{ZWNJ}روم",
                "expected": f"می{ZWNJ}روم",
                "options": {},
                "kind": "negative",
                "note": "Proper ZWNJ between prefix and verb must remain",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-011",
                "input": f"نمی{ZWNJ}دانم",
                "expected": f"نمی{ZWNJ}دانم",
                "options": {},
                "kind": "negative",
                "note": "Proper ZWNJ with prefix نمی",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-012",
                "input": f"کتاب{ZWNJ}ها",
                "expected": f"کتاب{ZWNJ}ها",
                "options": {},
                "kind": "negative",
                "note": "Proper ZWNJ with plural suffix ها",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-013",
                "input": f"دانش{ZWNJ}آموز",
                "expected": f"دانش{ZWNJ}آموز",
                "options": {},
                "kind": "negative",
                "note": "Proper compound noun with ZWNJ",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-014",
                "input": f"خانه{ZWNJ}ای",
                "expected": f"خانه{ZWNJ}ای",
                "options": {},
                "kind": "negative",
                "note": "Proper indefinite suffix with ZWNJ",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-015",
                "input": f"دست{ZWNJ}نوشته",
                "expected": f"دست{ZWNJ}نوشته",
                "options": {},
                "kind": "negative",
                "note": "Proper compound noun دست‌نوشته",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-016",
                "input": f"گفت{ZWNJ}وگو",
                "expected": f"گفت{ZWNJ}وگو",
                "options": {},
                "kind": "negative",
                "note": "Proper Persian standard compound گفت‌وگو",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-017",
                "input": f"پیش{ZWNJ}بینی",
                "expected": f"پیش{ZWNJ}بینی",
                "options": {},
                "kind": "negative",
                "note": "Proper compound word پیش‌بینی",
                "reviewed": False,
            },
            {
                "id": "zwnj-cleanup-018",
                "input": f"بین{ZWNJ}المللی",
                "expected": f"بین{ZWNJ}المللی",
                "options": {},
                "kind": "negative",
                "note": "Standard compound noun بین‌المللی",
                "reviewed": False,
            },
        ],
    }


def get_spaces_data():
    return {
        "rule": "spaces",
        "description_en": "Normalize multiple spaces and trailing spaces while preserving intentional line breaks.",
        "cases": [
            {
                "id": "spaces-001",
                "input": "سلام    جهان",
                "expected": "سلام جهان",
                "options": {},
                "kind": "positive",
                "note": "Collapse multiple horizontal spaces",
                "reviewed": False,
            },
            {
                "id": "spaces-002",
                "input": "این یک   متن آزمایشی است.",
                "expected": "این یک متن آزمایشی است.",
                "options": {},
                "kind": "positive",
                "note": "Collapse three spaces in sentence",
                "reviewed": False,
            },
            {
                "id": "spaces-003",
                "input": "کتاب و دفتر  ",
                "expected": "کتاب و دفتر",
                "options": {},
                "kind": "positive",
                "note": "Strip trailing whitespace",
                "reviewed": False,
            },
            {
                "id": "spaces-004",
                "input": "کتاب ، دفتر",
                "expected": "کتاب، دفتر",
                "options": {},
                "kind": "positive",
                "note": "Remove space before Persian comma",
                "reviewed": False,
            },
            {
                "id": "spaces-005",
                "input": "امروز شنبه است ؛ فردا یکشنبه.",
                "expected": "امروز شنبه است؛ فردا یکشنبه.",
                "options": {},
                "kind": "positive",
                "note": "Remove space before semicolon",
                "reviewed": False,
            },
            {
                "id": "spaces-006",
                "input": "آیا آماده هستید ؟",
                "expected": "آیا آماده هستید؟",
                "options": {},
                "kind": "positive",
                "note": "Remove space before question mark",
                "reviewed": False,
            },
            {
                "id": "spaces-007",
                "input": "به پیشواز بهار بروید !",
                "expected": "به پیشواز بهار بروید!",
                "options": {},
                "kind": "positive",
                "note": "Remove space before exclamation mark",
                "reviewed": False,
            },
            {
                "id": "spaces-008",
                "input": "موضوع جلسه : بررسی نهایی بودجه",
                "expected": "موضوع جلسه: بررسی نهایی بودجه",
                "options": {},
                "kind": "positive",
                "note": "Remove space before colon",
                "reviewed": False,
            },
            {
                "id": "spaces-009",
                "input": "پایان جمله رسید .",
                "expected": "پایان جمله رسید.",
                "options": {},
                "kind": "positive",
                "note": "Remove space before period",
                "reviewed": False,
            },
            {
                "id": "spaces-010",
                "input": "نکته اول . نکته دوم .",
                "expected": "نکته اول. نکته دوم.",
                "options": {},
                "kind": "positive",
                "note": "Remove multiple spaces before periods",
                "reviewed": False,
            },
            {
                "id": "spaces-011",
                "input": "پاراگراف اول.\n\nپاراگراف دوم.",
                "expected": "پاراگراف اول.\n\nپاراگراف دوم.",
                "options": {},
                "kind": "negative",
                "note": "Preserve intentional paragraph breaks",
                "reviewed": False,
            },
            {
                "id": "spaces-012",
                "input": "سطر اول\nسطر دوم",
                "expected": "سطر اول\nسطر دوم",
                "options": {},
                "kind": "negative",
                "note": "Preserve intentional single line break",
                "reviewed": False,
            },
            {
                "id": "spaces-013",
                "input": "یک دو سه چهار پنج",
                "expected": "یک دو سه چهار پنج",
                "options": {},
                "kind": "negative",
                "note": "Normal single spaces preserved",
                "reviewed": False,
            },
            {
                "id": "spaces-014",
                "input": "کتاب، دفتر، قلم و کاغذ",
                "expected": "کتاب، دفتر، قلم و کاغذ",
                "options": {},
                "kind": "negative",
                "note": "Properly spaced punctuation preserved",
                "reviewed": False,
            },
            {
                "id": "spaces-015",
                "input": "آیا آمدی؟ بله، آمدم.",
                "expected": "آیا آمدی؟ بله، آمدم.",
                "options": {},
                "kind": "negative",
                "note": "Standard question spacing preserved",
                "reviewed": False,
            },
            {
                "id": "spaces-016",
                "input": "نقطه. بعد از نقطه فاصله استاندارد است.",
                "expected": "نقطه. بعد از نقطه فاصله استاندارد است.",
                "options": {},
                "kind": "negative",
                "note": "Standard sentence boundary preserved",
                "reviewed": False,
            },
            {
                "id": "spaces-017",
                "input": "«گیومه» بدون فاصله اضافه است.",
                "expected": "«گیومه» بدون فاصله اضافه است.",
                "options": {},
                "kind": "negative",
                "note": "Correctly spaced quotes preserved",
                "reviewed": False,
            },
            {
                "id": "spaces-018",
                "input": "(پرانتز) بدون فاصله اضافه است.",
                "expected": "(پرانتز) بدون فاصله اضافه است.",
                "options": {},
                "kind": "negative",
                "note": "Correctly spaced parentheses preserved",
                "reviewed": False,
            },
        ],
    }


def get_punctuation_data():
    return {
        "rule": "punctuation",
        "description_en": "Convert ASCII punctuation (, ; ?) to Persian counterparts (، ؛ ؟) and enforce one space after and none before.",
        "cases": [
            {
                "id": "punctuation-001",
                "input": "سیب, گلابی, پرتقال",
                "expected": "سیب، گلابی، پرتقال",
                "options": {},
                "kind": "positive",
                "note": "English comma to Persian comma",
                "reviewed": False,
            },
            {
                "id": "punctuation-002",
                "input": "امروز شنبه است; فردا یکشنبه است.",
                "expected": "امروز شنبه است؛ فردا یکشنبه است.",
                "options": {},
                "kind": "positive",
                "note": "English semicolon to Persian semicolon",
                "reviewed": False,
            },
            {
                "id": "punctuation-003",
                "input": "آیا شما آمدید?",
                "expected": "آیا شما آمدید؟",
                "options": {},
                "kind": "positive",
                "note": "English question mark to Persian question mark",
                "reviewed": False,
            },
            {
                "id": "punctuation-004",
                "input": "سلام،من امروز آمدم.",
                "expected": "سلام، من امروز آمدم.",
                "options": {},
                "kind": "positive",
                "note": "Add missing space after Persian comma",
                "reviewed": False,
            },
            {
                "id": "punctuation-005",
                "input": "رفت؛اما زود برگشت.",
                "expected": "رفت؛ اما زود برگشت.",
                "options": {},
                "kind": "positive",
                "note": "Add missing space after Persian semicolon",
                "reviewed": False,
            },
            {
                "id": "punctuation-006",
                "input": "کجا رفتی؟خانه بودم.",
                "expected": "کجا رفتی؟ خانه بودم.",
                "options": {},
                "kind": "positive",
                "note": "Add missing space after Persian question mark",
                "reviewed": False,
            },
            {
                "id": "punctuation-007",
                "input": "ایران ,تهران",
                "expected": "ایران، تهران",
                "options": {},
                "kind": "positive",
                "note": "Convert comma and fix surrounding spacing",
                "reviewed": False,
            },
            {
                "id": "punctuation-008",
                "input": "دانشجو ,استاد",
                "expected": "دانشجو، استاد",
                "options": {},
                "kind": "positive",
                "note": "Fix punctuation spacing between words",
                "reviewed": False,
            },
            {
                "id": "punctuation-009",
                "input": "چرا?زیرا باران می‌بارید.",
                "expected": "چرا؟ زیرا باران می‌بارید.",
                "options": {},
                "kind": "positive",
                "note": "Convert question mark and insert space",
                "reviewed": False,
            },
            {
                "id": "punctuation-010",
                "input": "او گفت:من اینجا هستم.",
                "expected": "او گفت: من اینجا هستم.",
                "options": {},
                "kind": "positive",
                "note": "Add space after colon before speech",
                "reviewed": False,
            },
            {
                "id": "punctuation-011",
                "input": "عدد اعشاری 3.14 است.",
                "expected": "عدد اعشاری 3.14 است.",
                "options": {},
                "kind": "negative",
                "note": "Decimal dot must remain untouched",
                "reviewed": False,
            },
            {
                "id": "punctuation-012",
                "input": 'He said, "Hello; are you ready?"',
                "expected": 'He said, "Hello; are you ready?"',
                "options": {},
                "kind": "negative",
                "note": "English punctuation inside Latin sentence preserved",
                "reviewed": False,
            },
            {
                "id": "punctuation-013",
                "input": "url = https://example.com/search?q=test;sort=desc",
                "expected": "url = https://example.com/search?q=test;sort=desc",
                "options": {},
                "kind": "negative",
                "note": "Punctuation marks inside URL parameters must not change",
                "reviewed": False,
            },
            {
                "id": "punctuation-014",
                "input": "for (let i = 0; i < 10; i++)",
                "expected": "for (let i = 0; i < 10; i++)",
                "options": {},
                "kind": "negative",
                "note": "Code with semicolons must not change",
                "reviewed": False,
            },
            {
                "id": "punctuation-015",
                "input": "نسبت ریاضی ۱:۲ برقرار است.",
                "expected": "نسبت ریاضی ۱:۲ برقرار است.",
                "options": {},
                "kind": "negative",
                "note": "Mathematical ratio colon must not receive space",
                "reviewed": False,
            },
            {
                "id": "punctuation-016",
                "input": "جلسه در ساعت 14:30 برگزار می‌شود.",
                "expected": "جلسه در ساعت 14:30 برگزار می‌شود.",
                "options": {},
                "kind": "negative",
                "note": "Time format with colon must not receive space",
                "reviewed": False,
            },
            {
                "id": "punctuation-017",
                "input": "روزهای شنبه، یکشنبه و دوشنبه تعطیل نیستند.",
                "expected": "روزهای شنبه، یکشنبه و دوشنبه تعطیل نیستند.",
                "options": {},
                "kind": "negative",
                "note": "Already correct Persian commas and spacing",
                "reviewed": False,
            },
            {
                "id": "punctuation-018",
                "input": "چرا رفتی؟ مگر قرار نبود بمانی؟",
                "expected": "چرا رفتی؟ مگر قرار نبود بمانی؟",
                "options": {},
                "kind": "negative",
                "note": "Already correct Persian question mark and spacing",
                "reviewed": False,
            },
        ],
    }


def get_quotes_data():
    return {
        "rule": "quotes",
        "description_en": "Convert ASCII double quotes and English smart quotes to Persian guillemets (« ») in Persian context.",
        "cases": [
            {
                "id": "quotes-001",
                "input": 'او گفت "سلام"',
                "expected": "او گفت «سلام»",
                "options": {},
                "kind": "positive",
                "note": "ASCII quotes to Persian guillemets",
                "reviewed": False,
            },
            {
                "id": "quotes-002",
                "input": 'کتاب "گلستان سعدی" بسیار نفیس است.',
                "expected": "کتاب «گلستان سعدی» بسیار نفیس است.",
                "options": {},
                "kind": "positive",
                "note": "Book title quoted with ASCII quotes",
                "reviewed": False,
            },
            {
                "id": "quotes-003",
                "input": "واژه “پژوهش” در متن آمده است.",
                "expected": "واژه «پژوهش» در متن آمده است.",
                "options": {},
                "kind": "positive",
                "note": "English curly double quotes to guillemets",
                "reviewed": False,
            },
            {
                "id": "quotes-004",
                "input": "نام مقاله “فناوری نوین” است.",
                "expected": "نام مقاله «فناوری نوین» است.",
                "options": {},
                "kind": "positive",
                "note": "Article title with curly quotes",
                "reviewed": False,
            },
            {
                "id": "quotes-005",
                "input": 'عبارت "دانش توانایی است" از کیست؟',
                "expected": "عبارت «دانش توانایی است» از کیست؟",
                "options": {},
                "kind": "positive",
                "note": "Quoted sentence inside question",
                "reviewed": False,
            },
            {
                "id": "quotes-006",
                "input": 'او فریاد زد: "صبر کنید!"',
                "expected": "او فریاد زد: «صبر کنید!»",
                "options": {},
                "kind": "positive",
                "note": "Speech in quotation marks",
                "reviewed": False,
            },
            {
                "id": "quotes-007",
                "input": 'مفهوم "هوش مصنوعی" بسیار گسترده است.',
                "expected": "مفهوم «هوش مصنوعی» بسیار گسترده است.",
                "options": {},
                "kind": "positive",
                "note": "Technical term in quotation marks",
                "reviewed": False,
            },
            {
                "id": "quotes-008",
                "input": 'شعر "صد دانه یاقوت" معروف است.',
                "expected": "شعر «صد دانه یاقوت» معروف است.",
                "options": {},
                "kind": "positive",
                "note": "Poem title in quotation marks",
                "reviewed": False,
            },
            {
                "id": "quotes-009",
                "input": 'گفت: "فردا بازمی‌گردم."',
                "expected": "گفت: «فردا بازمی‌گردم.»",
                "options": {},
                "kind": "positive",
                "note": "Direct speech in quotation marks",
                "reviewed": False,
            },
            {
                "id": "quotes-010",
                "input": 'He said "Hello world" to everyone.',
                "expected": 'He said "Hello world" to everyone.',
                "options": {},
                "kind": "negative",
                "note": "Quotes inside English text preserved",
                "reviewed": False,
            },
            {
                "id": "quotes-011",
                "input": 'const message = "Hello";',
                "expected": 'const message = "Hello";',
                "options": {},
                "kind": "negative",
                "note": "Quotes in code line preserved",
                "reviewed": False,
            },
            {
                "id": "quotes-012",
                "input": '{"title": "data", "count": 1}',
                "expected": '{"title": "data", "count": 1}',
                "options": {},
                "kind": "negative",
                "note": "JSON-like string quotes preserved",
                "reviewed": False,
            },
            {
                "id": "quotes-013",
                "input": 'کد `console.log("test")` را بنویسید.',
                "expected": 'کد `console.log("test")` را بنویسید.',
                "options": {},
                "kind": "negative",
                "note": "Quotes inside inline code preserved",
                "reviewed": False,
            },
            {
                "id": "quotes-014",
                "input": "او گفت «سلام» و درود فرستاد.",
                "expected": "او گفت «سلام» و درود فرستاد.",
                "options": {},
                "kind": "negative",
                "note": "Already correct Persian guillemets preserved",
                "reviewed": False,
            },
            {
                "id": "quotes-015",
                "input": "کتاب «بوستان» اثر سعدی شیرازی است.",
                "expected": "کتاب «بوستان» اثر سعدی شیرازی است.",
                "options": {},
                "kind": "negative",
                "note": "Already correct book title in guillemets",
                "reviewed": False,
            },
            {
                "id": "quotes-016",
                "input": "«دانایی توانایی است» سخنی پرمایه است.",
                "expected": "«دانایی توانایی است» سخنی پرمایه است.",
                "options": {},
                "kind": "negative",
                "note": "Already correct Persian quote at start of sentence",
                "reviewed": False,
            },
        ],
    }


def get_brackets_spacing_data():
    return {
        "rule": "brackets-spacing",
        "description_en": "Enforce one space outside and no space inside brackets: () [] «». Protect code and Markdown.",
        "cases": [
            {
                "id": "brackets-spacing-001",
                "input": "کتاب ( گلستان ) ارزشمند است.",
                "expected": "کتاب (گلستان) ارزشمند است.",
                "options": {},
                "kind": "positive",
                "note": "Remove spaces inside parentheses",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-002",
                "input": "پروژه [ فاز اول ] تمام شد.",
                "expected": "پروژه [فاز اول] تمام شد.",
                "options": {},
                "kind": "positive",
                "note": "Remove spaces inside square brackets",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-003",
                "input": "متن « نقل قول » زیباست.",
                "expected": "متن «نقل قول» زیباست.",
                "options": {},
                "kind": "positive",
                "note": "Remove spaces inside guillemets",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-004",
                "input": "کلمه(توضیح بیشتر)",
                "expected": "کلمه (توضیح بیشتر)",
                "options": {},
                "kind": "positive",
                "note": "Add missing space before opening parenthesis",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-005",
                "input": "کلمه[پاورقی شماره یک]",
                "expected": "کلمه [پاورقی شماره یک]",
                "options": {},
                "kind": "positive",
                "note": "Add missing space before opening bracket",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-006",
                "input": "نکته«مهم و کلیدی»",
                "expected": "نکته «مهم و کلیدی»",
                "options": {},
                "kind": "positive",
                "note": "Add missing space before opening guillemet",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-007",
                "input": "( متن آزمایشی ) در پرانتز",
                "expected": "(متن آزمایشی) در پرانتز",
                "options": {},
                "kind": "positive",
                "note": "Remove spaces inside parentheses at line start",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-008",
                "input": "« گیومه باز و بسته » با فاصله",
                "expected": "«گیومه باز و بسته» با فاصله",
                "options": {},
                "kind": "positive",
                "note": "Remove inner spaces from guillemets",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-009",
                "input": "[ یادداشت اول ] نوشته شد.",
                "expected": "[یادداشت اول] نوشته شد.",
                "options": {},
                "kind": "positive",
                "note": "Remove inner spaces from square brackets",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-010",
                "input": "تابع foo(x) در برنامه فراخوانی شد.",
                "expected": "تابع foo(x) در برنامه فراخوانی شد.",
                "options": {},
                "kind": "negative",
                "note": "Function call syntax foo(x) preserved",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-011",
                "input": "آرایه arr[0] عنصر اول است.",
                "expected": "آرایه arr[0] عنصر اول است.",
                "options": {},
                "kind": "negative",
                "note": "Array subscript arr[0] preserved",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-012",
                "input": "پیوند [عنوان](https://example.com) در متن",
                "expected": "پیوند [عنوان](https://example.com) در متن",
                "options": {},
                "kind": "negative",
                "note": "Markdown link syntax preserved",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-013",
                "input": "الگوی regex شامل (?:abc) است.",
                "expected": "الگوی regex شامل (?:abc) است.",
                "options": {},
                "kind": "negative",
                "note": "Regular expression non-capturing group preserved",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-014",
                "input": "دانشگاه تهران (تأسیس ۱۳۱۳) کهن‌ترین دانشگاه مدرن ایران است.",
                "expected": "دانشگاه تهران (تأسیس ۱۳۱۳) کهن‌ترین دانشگاه مدرن ایران است.",
                "options": {},
                "kind": "negative",
                "note": "Already correctly spaced parentheses preserved",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-015",
                "input": "بند سوم [قانون اساسی] را مطالعه کنید.",
                "expected": "بند سوم [قانون اساسی] را مطالعه کنید.",
                "options": {},
                "kind": "negative",
                "note": "Already correctly spaced square brackets preserved",
                "reviewed": False,
            },
            {
                "id": "brackets-spacing-016",
                "input": "کتاب «گلستان» شاهکار نثر فارسی است.",
                "expected": "کتاب «گلستان» شاهکار نثر فارسی است.",
                "options": {},
                "kind": "negative",
                "note": "Already correctly spaced guillemets preserved",
                "reviewed": False,
            },
        ],
    }


def get_ellipsis_data():
    return {
        "rule": "ellipsis",
        "description_en": "Convert three or more ASCII dots (...) to the standard typographical ellipsis character (…), protecting code and URL ranges.",
        "cases": [
            {
                "id": "ellipsis-001",
                "input": "داستان ادامه دارد...",
                "expected": "داستان ادامه دارد…",
                "options": {},
                "kind": "positive",
                "note": "Three dots to ellipsis at sentence end",
                "reviewed": False,
            },
            {
                "id": "ellipsis-002",
                "input": "صبر کن.... گوش بده.",
                "expected": "صبر کن… گوش بده.",
                "options": {},
                "kind": "positive",
                "note": "Four dots collapsed to single ellipsis",
                "reviewed": False,
            },
            {
                "id": "ellipsis-003",
                "input": "شاید فردا... شاید هرگز...",
                "expected": "شاید فردا… شاید هرگز…",
                "options": {},
                "kind": "positive",
                "note": "Multiple ellipsis occurrences in one line",
                "reviewed": False,
            },
            {
                "id": "ellipsis-004",
                "input": "و غیره...",
                "expected": "و غیره…",
                "options": {},
                "kind": "positive",
                "note": "Common Persian abbreviation ending",
                "reviewed": False,
            },
            {
                "id": "ellipsis-005",
                "input": "سکوت برقرار شد...",
                "expected": "سکوت برقرار شد…",
                "options": {},
                "kind": "positive",
                "note": "Three dots at sentence end",
                "reviewed": False,
            },
            {
                "id": "ellipsis-006",
                "input": "یک، دو، سه...",
                "expected": "یک، دو، سه…",
                "options": {},
                "kind": "positive",
                "note": "Ellipsis following counting sequence",
                "reviewed": False,
            },
            {
                "id": "ellipsis-007",
                "input": "منتظر ماندیم... اما نیامد.",
                "expected": "منتظر ماندیم… اما نیامد.",
                "options": {},
                "kind": "positive",
                "note": "Ellipsis in mid-sentence pause",
                "reviewed": False,
            },
            {
                "id": "ellipsis-008",
                "input": "راه طولانی است...",
                "expected": "راه طولانی است…",
                "options": {},
                "kind": "positive",
                "note": "Trailing dots to ellipsis",
                "reviewed": False,
            },
            {
                "id": "ellipsis-009",
                "input": "امیدوار بودیم... بسیار امیدوار.",
                "expected": "امیدوار بودیم… بسیار امیدوار.",
                "options": {},
                "kind": "positive",
                "note": "Medial three dots to ellipsis",
                "reviewed": False,
            },
            {
                "id": "ellipsis-010",
                "input": "import ... from 'module'",
                "expected": "import ... from 'module'",
                "options": {},
                "kind": "negative",
                "note": "Code syntax with dots preserved",
                "reviewed": False,
            },
            {
                "id": "ellipsis-011",
                "input": "دامنه نسخه 1.2...1.5 بررسی شد.",
                "expected": "دامنه نسخه 1.2...1.5 بررسی شد.",
                "options": {},
                "kind": "negative",
                "note": "Version range notation preserved",
                "reviewed": False,
            },
            {
                "id": "ellipsis-012",
                "input": "پیوند https://example.com/.../path موجود است.",
                "expected": "پیوند https://example.com/.../path موجود است.",
                "options": {},
                "kind": "negative",
                "note": "Dots in URL path preserved",
                "reviewed": False,
            },
            {
                "id": "ellipsis-013",
                "input": "دستور const arr = [...items]; در جاوااسکریپت",
                "expected": "دستور const arr = [...items]; در جاوااسکریپت",
                "options": {},
                "kind": "negative",
                "note": "JavaScript spread operator [...items] preserved",
                "reviewed": False,
            },
            {
                "id": "ellipsis-014",
                "input": "نام پرونده test...txt بود.",
                "expected": "نام پرونده test...txt بود.",
                "options": {},
                "kind": "negative",
                "note": "Filename with dots preserved",
                "reviewed": False,
            },
            {
                "id": "ellipsis-015",
                "input": "داستان ادامه دارد… و پایان یافت.",
                "expected": "داستان ادامه دارد… و پایان یافت.",
                "options": {},
                "kind": "negative",
                "note": "Already correct standard ellipsis character preserved",
                "reviewed": False,
            },
            {
                "id": "ellipsis-016",
                "input": "سکوت و آرامش… همه جا را فرا گرفت.",
                "expected": "سکوت و آرامش… همه جا را فرا گرفت.",
                "options": {},
                "kind": "negative",
                "note": "Already correct typographic ellipsis preserved",
                "reviewed": False,
            },
        ],
    }


def get_kashida_data():
    return {
        "rule": "kashida",
        "description_en": "Remove decorative kashida (tatweel U+0640) from Persian words.",
        "cases": [
            {
                "id": "kashida-001",
                "input": "ســـلام دوستان",
                "expected": "سلام دوستان",
                "options": {},
                "kind": "positive",
                "note": "Remove kashida from سلام",
                "reviewed": False,
            },
            {
                "id": "kashida-002",
                "input": "با احــــترام فراوان",
                "expected": "با احترام فراوان",
                "options": {},
                "kind": "positive",
                "note": "Remove kashida from احترام",
                "reviewed": False,
            },
            {
                "id": "kashida-003",
                "input": "شهر بـــــزرگ",
                "expected": "شهر بزرگ",
                "options": {},
                "kind": "positive",
                "note": "Remove kashida from بزرگ",
                "reviewed": False,
            },
            {
                "id": "kashida-004",
                "input": "زبان فـــــارسی",
                "expected": "زبان فارسی",
                "options": {},
                "kind": "positive",
                "note": "Remove kashida from فارسی",
                "reviewed": False,
            },
            {
                "id": "kashida-005",
                "input": "شهر تـــــهران",
                "expected": "شهر تهران",
                "options": {},
                "kind": "positive",
                "note": "Remove kashida from تهران",
                "reviewed": False,
            },
            {
                "id": "kashida-006",
                "input": "استاد دانـــــشگاه",
                "expected": "استاد دانشگاه",
                "options": {},
                "kind": "positive",
                "note": "Remove kashida from دانشگاه",
                "reviewed": False,
            },
            {
                "id": "kashida-007",
                "input": "مطالعه کتـــــاب",
                "expected": "مطالعه کتاب",
                "options": {},
                "kind": "positive",
                "note": "Remove kashida from کتاب",
                "reviewed": False,
            },
            {
                "id": "kashida-008",
                "input": "کسب موفـــــقیت",
                "expected": "کسب موفقیت",
                "options": {},
                "kind": "positive",
                "note": "Remove kashida from موفقیت",
                "reviewed": False,
            },
            {
                "id": "kashida-009",
                "input": "همراه و دوســـــت قدیمی",
                "expected": "همراه و دوست قدیمی",
                "options": {},
                "kind": "positive",
                "note": "Remove kashida from دوست",
                "reviewed": False,
            },
            {
                "id": "kashida-010",
                "input": "سلام بر شما و درود بر روان پاک نیاکان",
                "expected": "سلام بر شما و درود بر روان پاک نیاکان",
                "options": {},
                "kind": "negative",
                "note": "Correct text without kashida preserved",
                "reviewed": False,
            },
            {
                "id": "kashida-011",
                "input": "کتابخانه ملی جمهوری اسلامی ایران",
                "expected": "کتابخانه ملی جمهوری اسلامی ایران",
                "options": {},
                "kind": "negative",
                "note": "Proper name without kashida preserved",
                "reviewed": False,
            },
            {
                "id": "kashida-012",
                "input": "دانشگاه فردوسی مشهد از مراکز کهن دانش است.",
                "expected": "دانشگاه فردوسی مشهد از مراکز کهن دانش است.",
                "options": {},
                "kind": "negative",
                "note": "Academic prose without kashida preserved",
                "reviewed": False,
            },
            {
                "id": "kashida-013",
                "input": "فرهنگستان زبان و ادب فارسی قوانین مصوب دارد.",
                "expected": "فرهنگستان زبان و ادب فارسی قوانین مصوب دارد.",
                "options": {},
                "kind": "negative",
                "note": "Standard sentence without kashida preserved",
                "reviewed": False,
            },
            {
                "id": "kashida-014",
                "input": "ادبیات کهن و معاصر گنجینه‌ای ارزشمند است.",
                "expected": "ادبیات کهن و معاصر گنجینه‌ای ارزشمند است.",
                "options": {},
                "kind": "negative",
                "note": "Prose without kashida preserved",
                "reviewed": False,
            },
            {
                "id": "kashida-015",
                "input": "پژوهش علمی و دقیق نیازمند شکیبایی است.",
                "expected": "پژوهش علمی و دقیق نیازمند شکیبایی است.",
                "options": {},
                "kind": "negative",
                "note": "Scientific prose without kashida preserved",
                "reviewed": False,
            },
            {
                "id": "kashida-016",
                "input": "خط نستعلیق اصیل‌ترین شیوه خوشنویسی ایرانی است.",
                "expected": "خط نستعلیق اصیل‌ترین شیوه خوشنویسی ایرانی است.",
                "options": {},
                "kind": "negative",
                "note": "Calligraphy description without kashida preserved",
                "reviewed": False,
            },
        ],
    }


def get_heh_ye_data():
    return {
        "rule": "heh-ye",
        "description_en": "Normalize ezafe after silent heh (ه ی) to hamza (هٔ) or ZWNJ+ye (هی) according to configuration.",
        "cases": [
            {
                "id": "heh-ye-001",
                "input": "خانه ی من",
                "expected": "خانهٔ من",
                "options": {"hehYeStyle": "hamza"},
                "kind": "positive",
                "note": "Convert خانه ی to خانهٔ (hamza option)",
                "reviewed": False,
            },
            {
                "id": "heh-ye-002",
                "input": "خانه ی من",
                "expected": f"خانه{ZWNJ}ی من",
                "options": {"hehYeStyle": "zwnj"},
                "kind": "positive",
                "note": "Convert خانه ی to خانه‌ی (zwnj option)",
                "reviewed": False,
            },
            {
                "id": "heh-ye-003",
                "input": "نامه ی اداری رسید.",
                "expected": "نامهٔ اداری رسید.",
                "options": {"hehYeStyle": "hamza"},
                "kind": "positive",
                "note": "Convert نامه ی to نامهٔ",
                "reviewed": False,
            },
            {
                "id": "heh-ye-004",
                "input": "نامه ی اداری رسید.",
                "expected": f"نامه{ZWNJ}ی اداری رسید.",
                "options": {"hehYeStyle": "zwnj"},
                "kind": "positive",
                "note": "Convert نامه ی to نامه‌ی",
                "reviewed": False,
            },
            {
                "id": "heh-ye-005",
                "input": "جامه ی نو بر تن کرد.",
                "expected": "جامهٔ نو بر تن کرد.",
                "options": {"hehYeStyle": "hamza"},
                "kind": "positive",
                "note": "Convert جامه ی to جامهٔ",
                "reviewed": False,
            },
            {
                "id": "heh-ye-006",
                "input": "پرونده ی پرونده ساز",
                "expected": "پروندهٔ پرونده ساز",
                "options": {"hehYeStyle": "hamza"},
                "kind": "positive",
                "note": "Convert پرونده ی to پروندهٔ",
                "reviewed": False,
            },
            {
                "id": "heh-ye-007",
                "input": "چشمه ی آب زلال",
                "expected": f"چشمه{ZWNJ}ی آب زلال",
                "options": {"hehYeStyle": "zwnj"},
                "kind": "positive",
                "note": "Convert چشمه ی to چشمه‌ی",
                "reviewed": False,
            },
            {
                "id": "heh-ye-008",
                "input": "هفته ی آینده دیدار داریم.",
                "expected": "هفتهٔ آینده دیدار داریم.",
                "options": {"hehYeStyle": "hamza"},
                "kind": "positive",
                "note": "Convert هفته ی to هفتهٔ",
                "reviewed": False,
            },
            {
                "id": "heh-ye-009",
                "input": "ستاره ی درخشان در آسمان",
                "expected": "ستارهٔ درخشان در آسمان",
                "options": {"hehYeStyle": "hamza"},
                "kind": "positive",
                "note": "Convert ستاره ی to ستارهٔ",
                "reviewed": False,
            },
            {
                "id": "heh-ye-010",
                "input": f"او در خانه{ZWNJ}ای بزرگ زندگی می‌کند.",
                "expected": f"او در خانه{ZWNJ}ای بزرگ زندگی می‌کند.",
                "options": {"hehYeStyle": "hamza"},
                "kind": "negative",
                "note": "Indefinite ya after heh (خانه‌ای) is not ezafe and must not change",
                "reviewed": False,
            },
            {
                "id": "heh-ye-011",
                "input": f"نامه{ZWNJ}ای به دستم رسید.",
                "expected": f"نامه{ZWNJ}ای به دستم رسید.",
                "options": {"hehYeStyle": "hamza"},
                "kind": "negative",
                "note": "Indefinite noun نامه‌ای must not change",
                "reviewed": False,
            },
            {
                "id": "heh-ye-012",
                "input": f"جامه{ZWNJ}ای زیبا دوخته شد.",
                "expected": f"جامه{ZWNJ}ای زیبا دوخته شد.",
                "options": {"hehYeStyle": "hamza"},
                "kind": "negative",
                "note": "Indefinite noun جامه‌ای must not change",
                "reviewed": False,
            },
            {
                "id": "heh-ye-013",
                "input": f"چشمه{ZWNJ}ای جوشان در کوهستان",
                "expected": f"چشمه{ZWNJ}ای جوشان در کوهستان",
                "options": {"hehYeStyle": "hamza"},
                "kind": "negative",
                "note": "Indefinite noun چشمه‌ای must not change",
                "reviewed": False,
            },
            {
                "id": "heh-ye-014",
                "input": f"دیده{ZWNJ}ای پر از اشک",
                "expected": f"دیده{ZWNJ}ای پر از اشک",
                "options": {"hehYeStyle": "hamza"},
                "kind": "negative",
                "note": "Participle دیده‌ای must not change",
                "reviewed": False,
            },
            {
                "id": "heh-ye-015",
                "input": f"خسته{ZWNJ}ای از راه رسید.",
                "expected": f"خسته{ZWNJ}ای از راه رسید.",
                "options": {"hehYeStyle": "hamza"},
                "kind": "negative",
                "note": "Adjective with indefinite ya خسته‌ای must not change",
                "reviewed": False,
            },
            {
                "id": "heh-ye-016",
                "input": "خانهٔ من بسیار دلنشین است.",
                "expected": "خانهٔ من بسیار دلنشین است.",
                "options": {"hehYeStyle": "hamza"},
                "kind": "negative",
                "note": "Already correct ezafe with hamza must not change",
                "reviewed": False,
            },
        ],
    }


def get_protected_spans_data():
    return {
        "rule": "protected-spans",
        "description_en": "Ensure URLs, emails, inline code, code blocks, @mentions, #hashtags, and Latin words remain byte-identical while normalizing surrounding Persian.",
        "cases": [
            {
                "id": "protected-spans-001",
                "input": "کتاب ها در آدرس https://example.com/books/v1?id=50 قرار دارند.",
                "expected": f"کتاب{ZWNJ}ها در آدرس https://example.com/books/v1?id=50 قرار دارند.",
                "options": {},
                "kind": "positive",
                "note": "URL is preserved exactly while کتاب ها gets ZWNJ",
                "reviewed": False,
            },
            {
                "id": "protected-spans-002",
                "input": "نامه را به ایمیل user123@domain.com می فرستم.",
                "expected": f"نامه را به ایمیل user123@domain.com می{ZWNJ}فرستم.",
                "options": {},
                "kind": "positive",
                "note": "Email is preserved exactly while می فرستم gets ZWNJ",
                "reviewed": False,
            },
            {
                "id": "protected-spans-003",
                "input": "کد `const count = 5;` را اجرا می کنم.",
                "expected": f"کد `const count = 5;` را اجرا می{ZWNJ}کنم.",
                "options": {},
                "kind": "positive",
                "note": "Inline code preserved while Persian verb is normalized",
                "reviewed": False,
            },
            {
                "id": "protected-spans-004",
                "input": "در توییتر به @tech_persian پیام می دهم.",
                "expected": f"در توییتر به @tech_persian پیام می{ZWNJ}دهم.",
                "options": {},
                "kind": "positive",
                "note": "Mention @tech_persian preserved exactly",
                "reviewed": False,
            },
            {
                "id": "protected-spans-005",
                "input": "مطلب با هشتگ #iran_2024 منتشر می شود.",
                "expected": f"مطلب با هشتگ #iran_2024 منتشر می{ZWNJ}شود.",
                "options": {},
                "kind": "positive",
                "note": "Hashtag preserved exactly",
                "reviewed": False,
            },
            {
                "id": "protected-spans-006",
                "input": "فایل MP3 در سال 1403 ساخته شد.",
                "expected": "فایل MP3 در سال ۱۴۰۳ ساخته شد.",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Latin token MP3 preserved while standalone year 1403 is converted",
                "reviewed": False,
            },
            {
                "id": "protected-spans-007",
                "input": "نسخه v2.1.0 با فرمت UTF8 آماده می باشد.",
                "expected": f"نسخه v2.1.0 با فرمت UTF8 آماده می{ZWNJ}باشد.",
                "options": {},
                "kind": "positive",
                "note": "Version and UTF8 token preserved while Persian verb gets ZWNJ",
                "reviewed": False,
            },
            {
                "id": "protected-spans-008",
                "input": "قطعه کد:\n```javascript\nconsole.log('test 123');\n```\nاجرا می شود.",
                "expected": f"قطعه کد:\n```javascript\nconsole.log('test 123');\n```\nاجرا می{ZWNJ}شود.",
                "options": {},
                "kind": "positive",
                "note": "Fenced code block preserved while surrounding Persian gets ZWNJ",
                "reviewed": False,
            },
            {
                "id": "protected-spans-009",
                "input": "نشانی http://site.com/api?user=ali;page=2 را باز می کند.",
                "expected": f"نشانی http://site.com/api?user=ali;page=2 را باز می{ZWNJ}کند.",
                "options": {},
                "kind": "positive",
                "note": "URL with query params preserved while Persian verb gets ZWNJ",
                "reviewed": False,
            },
            {
                "id": "protected-spans-010",
                "input": "https://github.com/user/repo/blob/main/README.md",
                "expected": "https://github.com/user/repo/blob/main/README.md",
                "options": {},
                "kind": "negative",
                "note": "Standalone URL must remain byte-identical",
                "reviewed": False,
            },
            {
                "id": "protected-spans-011",
                "input": "contact_support@company.org",
                "expected": "contact_support@company.org",
                "options": {},
                "kind": "negative",
                "note": "Standalone email address must remain byte-identical",
                "reviewed": False,
            },
            {
                "id": "protected-spans-012",
                "input": '`git commit -m "feat: initial commit"`',
                "expected": '`git commit -m "feat: initial commit"`',
                "options": {},
                "kind": "negative",
                "note": "Inline code block must remain byte-identical",
                "reviewed": False,
            },
            {
                "id": "protected-spans-013",
                "input": "```javascript\nconst x = 10;\nconst y = 20;\n```",
                "expected": "```javascript\nconst x = 10;\nconst y = 20;\n```",
                "options": {},
                "kind": "negative",
                "note": "Standalone fenced code block must remain byte-identical",
                "reviewed": False,
            },
            {
                "id": "protected-spans-014",
                "input": "@developer_team",
                "expected": "@developer_team",
                "options": {},
                "kind": "negative",
                "note": "Standalone mention must remain byte-identical",
                "reviewed": False,
            },
            {
                "id": "protected-spans-015",
                "input": "#persian_typography_1403",
                "expected": "#persian_typography_1403",
                "options": {},
                "kind": "negative",
                "note": "Standalone hashtag must remain byte-identical",
                "reviewed": False,
            },
            {
                "id": "protected-spans-016",
                "input": "iPhone 15 Pro Max 256GB",
                "expected": "iPhone 15 Pro Max 256GB",
                "options": {},
                "kind": "negative",
                "note": "Latin brand string with numbers must remain byte-identical",
                "reviewed": False,
            },
        ],
    }


def get_combined_data():
    return {
        "rule": "combined",
        "description_en": "Paragraph-level test cases where 3 to 6 normalization rules apply concurrently.",
        "cases": [
            {
                "id": "combined-001",
                "input": 'علي و مهدي در سال 1403 کتاب ها را به کلاس می برند ,اما "گلستان" را فراموش کردند...',
                "expected": f"علی و مهدی در سال ۱۴۰۳ کتاب{ZWNJ}ها را به کلاس می{ZWNJ}برند، اما «گلستان» را فراموش کردند…",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Rules: arabic-letters, digits, zwnj, punctuation, quotes, ellipsis",
                "reviewed": False,
            },
            {
                "id": "combined-002",
                "input": 'آیا شما می دانید که خانه ی پدری بزرگ تر از خانه های دیگر است?بله ,مي دانم.',
                "expected": f"آیا شما می{ZWNJ}دانید که خانهٔ پدری بزرگ{ZWNJ}تر از خانه{ZWNJ}های دیگر است؟ بله، می{ZWNJ}دانم.",
                "options": {"hehYeStyle": "hamza"},
                "kind": "positive",
                "note": "Rules: zwnj, heh-ye, punctuation, arabic-letters",
                "reviewed": False,
            },
            {
                "id": "combined-003",
                "input": "كودك در بانك ٥٠٠٠ تومان پرداخت کرد ;اما رسيد دريافت نكرد...",
                "expected": "کودک در بانک ۵۰۰۰ تومان پرداخت کرد؛ اما رسید دریافت نکرد…",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Rules: arabic-letters, digits, punctuation, ellipsis",
                "reviewed": False,
            },
            {
                "id": "combined-004",
                "input": 'ســـلام!نسخه جدید v1.0.4 منتشر شد.برای دریافت فایل MP3 به آدرس https://example.com/dl بروید...',
                "expected": "سلام! نسخه جدید v1.0.4 منتشر شد. برای دریافت فایل MP3 به آدرس https://example.com/dl بروید…",
                "options": {},
                "kind": "positive",
                "note": "Rules: kashida, punctuation, protected-spans, ellipsis",
                "reviewed": False,
            },
            {
                "id": "combined-005",
                "input": 'او گفت "دانش توانایی است" ;اما نادانان نمی دانند...',
                "expected": f"او گفت «دانش توانایی است»؛ اما نادانان نمی{ZWNJ}دانند…",
                "options": {},
                "kind": "positive",
                "note": "Rules: quotes, punctuation, zwnj, ellipsis",
                "reviewed": False,
            },
            {
                "id": "combined-006",
                "input": f"پروژه ( فاز 2 ) در تاریخ 1403/01/15 تمام می شود .آیا راضی هستید ?",
                "expected": f"پروژه (فاز ۲) در تاریخ ۱۴۰۳/۰۱/۱۵ تمام می{ZWNJ}شود. آیا راضی هستید؟",
                "options": {"digits": "persian"},
                "kind": "positive",
                "note": "Rules: brackets-spacing, digits, zwnj, spaces, punctuation",
                "reviewed": False,
            },
            {
                "id": "combined-007",
                "input": f"منت خدای را عز و جل که طاعتش موجب قربت است و به شکر اندرش مزید نعمت. هر نفسی که فرو می{ZWNJ}رود ممد حیات است.",
                "expected": f"منت خدای را عز و جل که طاعتش موجب قربت است و به شکر اندرش مزید نعمت. هر نفسی که فرو می{ZWNJ}رود ممد حیات است.",
                "options": {},
                "kind": "negative",
                "note": "Clean classical prose (Saadi) with zero errors",
                "reviewed": False,
            },
            {
                "id": "combined-008",
                "input": "به نام خداوند جان و خرد، کزین برتر اندیشه برنگذرد. خداوند نام و خداوند جای، خداوند روزی‌ده و رهنمای.",
                "expected": "به نام خداوند جان و خرد، کزین برتر اندیشه برنگذرد. خداوند نام و خداوند جای، خداوند روزی‌ده و رهنمای.",
                "options": {},
                "kind": "negative",
                "note": "Clean epic verse (Ferdowsi) with zero errors",
                "reviewed": False,
            },
            {
                "id": "combined-009",
                "input": f"کهکشان راه شیری شامل میلیاردها ستاره است که حول یک مرکز مشترک گردش می{ZWNJ}کنند و سامانه‌های سیاره‌ای گوناگونی دارند.",
                "expected": f"کهکشان راه شیری شامل میلیاردها ستاره است که حول یک مرکز مشترک گردش می{ZWNJ}کنند و سامانه‌های سیاره‌ای گوناگونی دارند.",
                "options": {},
                "kind": "negative",
                "note": "Clean modern scientific prose with zero errors",
                "reviewed": False,
            },
            {
                "id": "combined-010",
                "input": "معماری سنتی ایران در شهرهایی چون اصفهان و یزد نمونه‌ای بی‌همتا از تلفیق اقلیم، بادگیرها و حیاط‌های مرکزی سرسبز است.",
                "expected": "معماری سنتی ایران در شهرهایی چون اصفهان و یزد نمونه‌ای بی‌همتا از تلفیق اقلیم، بادگیرها و حیاط‌های مرکزی سرسبز است.",
                "options": {},
                "kind": "negative",
                "note": "Clean architectural essay prose with zero errors",
                "reviewed": False,
            },
        ],
    }


# ==============================================================================
# 4. AI Evaluation Samples (6 Realistic Pairs)
# ==============================================================================

AI_SAMPLES = [
    {
        "sample": "01-formal-email",
        "text": (
            f"جناب آقای مهندس رضایی، مدیر محترم توسعه فناوری\n\n"
            f"با سلام و احترام،\n\n"
            f"پیرو گفت‌وگوهای پیشین پیرامون بازنگری در معماری سامانه، لازم به ذکر و یادآوری مجدد است که باید توجه داشت که "
            f"تیم‌های تخصصی در حال حاضر بر روی ارتقای زیرساخت متمرکز هستند. در پایان روز همه اعضای حاضر در جلسه باید نسبت به اهداف فصلی پاسخگو باشند "
            f"تا اطمینان حاصل کنیم که همگی بر روی یک صفحه یکسان هستیم و دیدگاه‌های متفاوتی وجود ندارد. "
            f"به همین جهت، بسیار حیاتی است که در جلسه روز دوشنبه آینده در ساعت ده صبح بتوانیم یک تصمیم مهم را بسازیم تا نقشه راه نهایی گردد.\n\n"
            f"گزارش عملکرد ماهانه نیز توسط تیم فنی ما تهیه و تکمیل شد و نسخه پی‌دی‌اف آن ضمیمه این نامه گردیده است. "
            f"ما برای دیدار با جنابعالی نگاه به جلو داریم تا گام‌های پیش رو را به شکل همه‌جانبه بررسی نماییم.\n\n"
            f"با تشکر و تجدید احترام،\n"
            f"حمید صابری"
        ),
        "expected": {
            "sample": "01-formal-email",
            "source": "synthetic",
            "issues": [
                {
                    "quote": "در پایان روز",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "در نهایت",
                    "explanation_fa": "گرته‌برداری مستقیم از اصطلاح انگلیسی at the end of the day",
                    "must_detect": True,
                },
                {
                    "quote": "بر روی یک صفحه یکسان هستیم",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "دیدگاه مشترکی داریم",
                    "explanation_fa": "ترجمه تحت‌اللفظی از عبارت on the same page",
                    "must_detect": True,
                },
                {
                    "quote": "یک تصمیم مهم را بسازیم",
                    "category": "collocation",
                    "severity": "error",
                    "suggestion": "تصمیم مهمی بگیریم",
                    "explanation_fa": "همایندی نادرست فعل ساختن با تصمیم (کالک make a decision)",
                    "must_detect": True,
                },
                {
                    "quote": "توسط تیم فنی ما تهیه و تکمیل شد",
                    "category": "grammar",
                    "severity": "warning",
                    "suggestion": "تیم فنی ما تهیه و تکمیل کرد",
                    "explanation_fa": "کاربرد ساختار مجهول انگلیسی با حرف اضافه توسط به جای ساختار معلوم طبیعی",
                    "must_detect": True,
                },
                {
                    "quote": "لازم به ذکر و یادآوری مجدد است که باید توجه داشت که",
                    "category": "redundancy",
                    "severity": "suggestion",
                    "suggestion": "شایان ذکر است که",
                    "explanation_fa": "اطناب و حشو بیهوده در آغاز جمله اداری",
                    "must_detect": False,
                },
                {
                    "quote": "نگاه به جلو داریم",
                    "category": "translationese",
                    "severity": "warning",
                    "suggestion": "مشتاقانه منتظریم",
                    "explanation_fa": "گرته‌برداری از عبارت انگلیسی look forward to",
                    "must_detect": False,
                },
            ],
            "reviewed": False,
        },
    },
    {
        "sample": "02-linkedin-post",
        "text": (
            f"بسیار خرسندم اعلام کنم که پس از شش ماه تلاش شبانه‌روزی، محصول ابری جدید شرکت به صورت رسمی رونمایی شد. "
            f"این دستاورد یک بازی‌تغییر واقعی است برای تمامی کسب‌وکارهایی که می‌خواهند فرآیندهای مالی خود را خودکار کنند. "
            f"در این مسیر، هر کدام از همکاران نقش کلیدی را بازی کرد تا بتوانیم سامانه‌ای مقیاس‌پذیر و پایدار خلق کنیم. "
            f"امیدواریم این پلتفرم بتواند یک تفاوت بزرگ ایجاد کند و هزینه‌های جاری را به حداقل برساند. "
            f"سرانجام دیروز با موفقیت ارسال کردیم پروژه نهایی را به سرورهای تولید و بازخوردهای نخستین فراتر از انتظار بود. "
            f"در مواجهه با این میزان استقبال، احساسات من غرق شده است و کلمات قادر به بیان حجم قدردانی من نیستند. "
            f"به عنوان یک توسعه‌دهنده نرم‌افزار همواره بر این باورم که پشتکار رمز پیروزی است و یک برنامه‌نویس باید پیوسته بیاموزد."
        ),
        "expected": {
            "sample": "02-linkedin-post",
            "source": "synthetic",
            "issues": [
                {
                    "quote": "یک بازی‌تغییر واقعی است",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "تحولی بنیادین به شمار می‌رود",
                    "explanation_fa": "گرته‌برداری ناشیانه از واژه مرکب انگلیسی game-changer",
                    "must_detect": True,
                },
                {
                    "quote": "نقش کلیدی را بازی کرد",
                    "category": "collocation",
                    "severity": "error",
                    "suggestion": "نقش کلیدی ایفا کرد",
                    "explanation_fa": "همایندی غلط فعل بازی کردن برای نقش (کالک play a role)",
                    "must_detect": True,
                },
                {
                    "quote": "یک تفاوت بزرگ ایجاد کند",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "تأثیر چشمگیری بگذارد",
                    "explanation_fa": "ترجمه تحت‌اللفظی از اصطلاح make a difference",
                    "must_detect": True,
                },
                {
                    "quote": "ارسال کردیم پروژه نهایی را به سرورهای تولید",
                    "category": "grammar",
                    "severity": "error",
                    "suggestion": "پروژه نهایی را به سرورهای تولید ارسال کردیم",
                    "explanation_fa": "برهم خوردن ترتیب اجزای جمله فارسی و قرار گرفتن فعل قبل از مفعول صریح",
                    "must_detect": True,
                },
                {
                    "quote": "احساسات من غرق شده است",
                    "category": "unnatural",
                    "severity": "warning",
                    "suggestion": "بسیار شگفت‌زده و سرشار از شوق هستم",
                    "explanation_fa": "ترجمه تحت‌اللفظی و غیرطبیعی از عبارت I am overwhelmed",
                    "must_detect": False,
                },
                {
                    "quote": "توسعه‌دهنده نرم‌افزار",
                    "category": "terminology",
                    "severity": "suggestion",
                    "suggestion": "توسعه‌دهنده نرم‌افزار",
                    "explanation_fa": "ناهماهنگی اصطلاحی در متن واحد با کاربرد همزمان توسعه‌دهنده نرم‌افزار و برنامه‌نویس",
                    "must_detect": False,
                },
            ],
            "reviewed": False,
        },
    },
    {
        "sample": "03-translated-tech-article",
        "text": (
            f"معماری میکروسرویس در سال‌های اخیر به استاندارد دفاکتوی توسعه سامانه‌های سازمانی بدل گشته است. "
            f"تقسیم کردن یک سامانه یکپارچه به اجزای مستقل کاملاً حس می‌سازد، به‌ویژه زمانی که تیم‌ها در مقیاس بالا فعالیت می‌کنند. "
            f"در حالی که این الگو استقلال عملیاتی بالایی به ارمغان می‌آورد، چالش‌های ارتباطی شبکه نیز به چشم می‌آید. "
            f"در این ساختار، پیام‌ها توسط سرویس‌ها پردازش می‌شوند تا تراکنش‌های توزیع‌شده با پایگاه داده مرکزی هماهنگ شوند. "
            f"هر عضو سامانه باید عملکرد بالایی را به نمایش بگذارد تا از گلوگاه‌های عملکردی جلوگیری شود. "
            f"مهندسان نرم‌افزار معمولاً از صف‌های پیام ناهمگام و ابزارهای پایش سلامت بهره می‌برند تا پایداری و تاب‌آوری کلی سامانه را ارتقا بخشند. "
            f"با این همه، اتصال پی‌درپی سرویس‌ها به دیتابیس می‌تواند پیچیدگی زیرساخت را افزایش دادن و هزینه‌های نگهداری را دوچندان سازد."
        ),
        "expected": {
            "sample": "03-translated-tech-article",
            "source": "synthetic",
            "issues": [
                {
                    "quote": "حس می‌سازد",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "کاملاً منطقی به نظر می‌رسد",
                    "explanation_fa": "ترجمه کلمه‌به‌کلمه و بی‌معنی از اصطلاح make sense",
                    "must_detect": True,
                },
                {
                    "quote": "در حالی که این الگو استقلال عملیاتی بالایی به ارمغان می‌آورد،",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "اگرچه این الگو استقلال عملیاتی بالایی به ارمغان می‌آورد، اما",
                    "explanation_fa": "گرته‌برداری ساختاری از کاربرد تقابلی while در زبان انگلیسی",
                    "must_detect": True,
                },
                {
                    "quote": "عملکرد بالایی را به نمایش بگذارد",
                    "category": "unnatural",
                    "severity": "warning",
                    "suggestion": "کارایی بالایی داشته باشد",
                    "explanation_fa": "کاربرد عبارت متکلف و غیرطبیعی برای بیان راندمان سیستم",
                    "must_detect": True,
                },
                {
                    "quote": "پیچیدگی زیرساخت را افزایش دادن",
                    "category": "grammar",
                    "severity": "error",
                    "suggestion": "پیچیدگی زیرساخت را افزایش دهد",
                    "explanation_fa": "به‌کارگیری نادرست مصدر به جای فعل التزامی متصرف در بند پیرو",
                    "must_detect": True,
                },
                {
                    "quote": "توسط سرویس‌ها پردازش می‌شوند",
                    "category": "grammar",
                    "severity": "warning",
                    "suggestion": "سرویس‌ها پردازش می‌کنند",
                    "explanation_fa": "استفاده از مجهول همراه با فاعل به شیوه ترجمه انگلیسی",
                    "must_detect": False,
                },
                {
                    "quote": "دیتابیس",
                    "category": "terminology",
                    "severity": "warning",
                    "suggestion": "پایگاه داده",
                    "explanation_fa": "ناهماهنگی اصطلاحی در متن؛ کاربرد همزمان دیتابیس و پایگاه داده",
                    "must_detect": False,
                },
            ],
            "reviewed": False,
        },
    },
    {
        "sample": "04-customer-support",
        "text": (
            f"کاربر گرامی،\n\n"
            f"از اینکه با مرکز پشتیبانی مشتریان ما تماس حاصل نمودید بسیار سپاسگزاریم. "
            f"ما عمیقاً متأسف هستیم برای هر ناراحتی که این موضوع ممکن است سبب شده باشد و وضعیت ایجادشده را به دقت بررسی کردیم. "
            f"بسته سفارش شما در حال حاضر در دست اقدام است توسط بخش انبارداری و پیش‌بینی می‌کنیم ظرف چهل و هشت ساعت آینده تحویل پست گردد. "
            f"همکاران ما مرسوله را با نهایت دقت بسته‌بندی کرده‌اند تا هیچ‌گونه آسیبی در طول مسیر به کالا وارد نیاید. "
            f"خواهشمند است یک چشم روی سفارش خود نگه دارید تا به محض تغییر کد رهگیری مطلع شوید. "
            f"تیم ما همیشه به پرداختن توجه کامل به بازخورد مشتریان متعهد است و نظر شما کیفیت خدمات را ارتقا می‌دهد. "
            f"امیدواریم شما یک روز شگفت‌انگیز داشته باشید و در صورت وجود هرگونه پرسش دیگر آماده پاسخگویی هستیم."
        ),
        "expected": {
            "sample": "04-customer-support",
            "source": "synthetic",
            "issues": [
                {
                    "quote": "ما عمیقاً متأسف هستیم برای هر ناراحتی که این موضوع ممکن است سبب شده باشد",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "از بابت مشکل پیش‌آمده صمیمانه پوزش می‌طلبیم",
                    "explanation_fa": "ترجمه لفظی و گرته‌برداری‌شده از کلیشه انگلیسی We are deeply sorry for any inconvenience...",
                    "must_detect": True,
                },
                {
                    "quote": "یک چشم روی سفارش خود نگه دارید",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "وضعیت سفارش خود را پیگیری کنید",
                    "explanation_fa": "ترجمه مضحک و تحت‌اللفظی از اصطلاح keep an eye on",
                    "must_detect": True,
                },
                {
                    "quote": "پرداختن توجه کامل به بازخورد",
                    "category": "collocation",
                    "severity": "error",
                    "suggestion": "توجه ویژه به بازخورد",
                    "explanation_fa": "همایندی غلط پرداختن برای توجه (کالک pay attention)",
                    "must_detect": True,
                },
                {
                    "quote": "در حال حاضر در دست اقدام است توسط بخش انبارداری",
                    "category": "grammar",
                    "severity": "warning",
                    "suggestion": "در بخش انبارداری در دست اقدام است",
                    "explanation_fa": "ترتیب ناهمگون اجزای جمله و کاربرد متمم عاملی توسط پس از مسند",
                    "must_detect": False,
                },
                {
                    "quote": "امیدواریم شما یک روز شگفت‌انگیز داشته باشید",
                    "category": "unnatural",
                    "severity": "warning",
                    "suggestion": "با آرزوی اوقاتی خوش برای شما",
                    "explanation_fa": "گرته‌برداری غیرفارسی از تعارف انگلیسی Have a wonderful day",
                    "must_detect": False,
                },
            ],
            "reviewed": False,
        },
    },
    {
        "sample": "05-product-description",
        "text": (
            f"بازی را تغییر دهید با این هدفون بی‌سیم پیشرفته که تعریف تازه‌ای از موسیقی ارائه می‌دهد. "
            f"در پایان روز کیفیت صدا تنها چیزی است که برای علاقه‌مندان موسیقی اهمیت دارد و این دستگاه پاسخگوی آن است. "
            f"مهندسان صدا با دقت بسیار کیفیت صدای شفاف و بی‌پایان را طراحی کرده‌اند تا ریزترین جزئیات نت‌ها شنیده شود. "
            f"این دستگاه با بهره‌گیری از جدیدترین استانداردهای ارتباطی به آسانی با انواع گوشی‌های هوشمند و تبلت‌ها هماهنگ می‌گردد. "
            f"همچنین باتری آن قادر به ارائه ده ساعت پخش مداوم است بدون اینکه نیاز به شارژ مجدد پیدا کند. "
            f"دوام باتری این محصول در شرایط آزمایشی سنجیده شده و طول عمر باتری دستگاه خیال شما را در سفرهای طولانی آسوده می‌سازد. "
            f"طراحی ارگونومیک بدنه تضمین می‌کند که گوش شما در استفاده ممتد دچار خستگی نگردد."
        ),
        "expected": {
            "sample": "05-product-description",
            "source": "synthetic",
            "issues": [
                {
                    "quote": "بازی را تغییر دهید با این هدفون",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "تجربه‌ای کاملاً متمایز با این هدفون داشته باشید",
                    "explanation_fa": "گرته‌برداری تبلیغاتی از عبارت change the game",
                    "must_detect": True,
                },
                {
                    "quote": "در پایان روز کیفیت صدا تنها چیزی است که",
                    "category": "translationese",
                    "severity": "error",
                    "suggestion": "در نهایت کیفیت صدا تنها عاملی است که",
                    "explanation_fa": "گرته‌برداری مستقیم از اصطلاح انگلیسی at the end of the day",
                    "must_detect": True,
                },
                {
                    "quote": "کیفیت صدای شفاف و بی‌پایان",
                    "category": "collocation",
                    "severity": "error",
                    "suggestion": "کیفیت صدای شفاف و بی‌نقص",
                    "explanation_fa": "همایندی نامفهوم و غیرطبیعی صفت بی‌پایان برای کیفیت صدا",
                    "must_detect": True,
                },
                {
                    "quote": "باتری آن قادر به ارائه ده ساعت پخش مداوم است",
                    "category": "unnatural",
                    "severity": "warning",
                    "suggestion": "باتری آن تا ده ساعت پخش مداوم را پشتیبانی می‌کند",
                    "explanation_fa": "ترجمه ثقیل و مصنوعی از ساختار is capable of providing",
                    "must_detect": False,
                },
                {
                    "quote": "طول عمر باتری",
                    "category": "terminology",
                    "severity": "suggestion",
                    "suggestion": "دوام باتری",
                    "explanation_fa": "ناهماهنگی اصطلاحی با کاربرد همزمان دوام باتری و طول عمر باتری برای مفهوم میزان شارژدهی",
                    "must_detect": False,
                },
            ],
            "reviewed": False,
        },
    },
    {
        "sample": "06-mixed-register",
        "text": (
            f"فرهنگ سازمانی و روحیه کار تیمی همواره از ارکان بنیادی پیشرفت شرکت ما به شمار می‌آید. "
            f"ما توی این شرکت خیلی هوای همدیگه رو داریم و سعی می‌کنیم در محیطی صمیمی پیشرفت کنیم. "
            f"در راستای تحقق اهداف استراتژیک سازمان و توسعه سازمانی که بسیار مهم است، برنامه‌ریزی دقیقی تدوین گردیده است. "
            f"جلسات ماهانه برای ارزیابی عملکرد برگزار می‌شود تا نقاط قوت و ضعف فرآیندها شناسایی گردد. "
            f"با این وجود، وقتی ضرب‌الاجل‌ها فشرده میشه بچه‌ها حسابی سنگ تموم می‌ذارن تا کار سروقت آماده بشه. "
            f"برای هماهنگی هرچه بهتر میان کارمندان مقیم و دورکار، جلسات رو آنلاین برگزار می‌کنیم تا در وقت و هزینه صرفه‌جویی شود. "
            f"کارشناسان منابع انسانی تأکید دارند که این موضوع می‌تواند تأثیرات منفی را بر انگیزه شغلی افراد بگذارد "
            f"و بنابراین باید اعتدال میان کار و زندگی شخصی حفظ گردد."
        ),
        "expected": {
            "sample": "06-mixed-register",
            "source": "synthetic",
            "issues": [
                {
                    "quote": "ما توی این شرکت خیلی هوای همدیگه رو داریم",
                    "category": "register",
                    "severity": "error",
                    "suggestion": "در این شرکت همکاران همواره پشتیبان یکدیگر هستند",
                    "explanation_fa": "افت ناگهانی لحن از نوشتاری اداری به عامیانه محاوره‌ای",
                    "must_detect": True,
                },
                {
                    "quote": "بچه‌ها حسابی سنگ تموم می‌ذارن تا کار سروقت آماده بشه",
                    "category": "register",
                    "severity": "error",
                    "suggestion": "اعضای تیم نهایت تلاش خود را به کار می‌بندند تا پروژه در موعد مقرر تکمیل گردد",
                    "explanation_fa": "ورود تعابیر و افعال کاملاً گفتاری به درون متن رسمی",
                    "must_detect": True,
                },
                {
                    "quote": "جلسات رو آنلاین برگزار می‌کنیم",
                    "category": "register",
                    "severity": "error",
                    "suggestion": "جلسات را به صورت برخط برگزار می‌کنیم",
                    "explanation_fa": "استفاده از نشانه محاوره‌ای «رو» و واژه عامیانه آنلاین در متن اداری",
                    "must_detect": True,
                },
                {
                    "quote": "در راستای تحقق اهداف استراتژیک سازمان و توسعه سازمانی که بسیار مهم است،",
                    "category": "redundancy",
                    "severity": "warning",
                    "suggestion": "در جهت تحقق اهداف راهبردی شرکت،",
                    "explanation_fa": "اطناب و حشو اداری خسته‌کننده در تضاد با جملات محاوره‌ای همجوار",
                    "must_detect": False,
                },
                {
                    "quote": "تأثیرات منفی را بر انگیزه شغلی افراد بگذارد",
                    "category": "grammar",
                    "severity": "warning",
                    "suggestion": "تأثیرات منفی بر انگیزه شغلی افراد بگذارد",
                    "explanation_fa": "آوردن نشانه مفعولی «را» بدون ضرورت برای اسم نکره موصوف",
                    "must_detect": False,
                },
            ],
            "reviewed": False,
        },
    },
]


# ==============================================================================
# 5. Generator Execution & Validation
# ==============================================================================


def generate_all_fixtures():
    files_created = 0
    rule_stats = {}

    # Create Schemas
    schema_dir = FIXTURES_DIR / "schema"
    write_file(
        schema_dir / "normalizer-cases.schema.json",
        dump_json_with_zwnj_escapes(NORMALIZER_CASES_SCHEMA),
    )
    write_file(
        schema_dir / "ai-sample-expected.schema.json",
        dump_json_with_zwnj_escapes(AI_SAMPLE_EXPECTED_SCHEMA),
    )
    files_created += 2

    # Create Clean Docs README
    clean_dir = FIXTURES_DIR / "clean"
    write_file(clean_dir / "README.md", CLEAN_README_MD)
    files_created += 1

    # Create Fixtures Root README
    write_file(FIXTURES_DIR / "README.md", FIXTURES_README_MD)
    files_created += 1

    # Create Normalizer JSON files
    normalizer_dir = FIXTURES_DIR / "normalizer"
    normalizer_generators = [
        get_arabic_letters_data,
        get_digits_data,
        get_zwnj_data,
        get_zwnj_cleanup_data,
        get_spaces_data,
        get_punctuation_data,
        get_quotes_data,
        get_brackets_spacing_data,
        get_ellipsis_data,
        get_kashida_data,
        get_heh_ye_data,
        get_protected_spans_data,
        get_combined_data,
    ]

    for gen in normalizer_generators:
        data = gen()
        rule_name = data["rule"]
        cases = data["cases"]
        total_cases = len(cases)
        negatives = sum(1 for c in cases if c["kind"] == "negative")
        neg_ratio = negatives / total_cases

        # Assert strict quality rules
        if rule_name == "combined":
            if total_cases != 10:
                raise ValueError(
                    f"combined.json must contain exactly 10 cases, got {total_cases}"
                )
        else:
            if not (15 <= total_cases <= 25):
                raise ValueError(
                    f"{rule_name}.json must contain 15 to 25 cases, got {total_cases}"
                )

        if neg_ratio < 0.40:
            raise ValueError(
                f"{rule_name}.json negative ratio is {neg_ratio:.2f}, must be >= 0.40"
            )

        for case in cases:
            if not re.match(r"^[a-z-]+-\d{3}$", case["id"]):
                raise ValueError(f"Invalid case id format: {case['id']}")
            if case["reviewed"] is not False:
                raise ValueError(
                    f"Case {case['id']} reviewed must be False initially"
                )
            if (
                case["kind"] == "negative"
                and case["input"] != case["expected"]
            ):
                raise ValueError(
                    f"Negative case {case['id']} must have identical input and expected"
                )

        file_path = normalizer_dir / f"{rule_name}.json"
        write_file(file_path, dump_json_with_zwnj_escapes(data))
        files_created += 1
        rule_stats[rule_name] = {
            "total": total_cases,
            "positive": total_cases - negatives,
            "negative": negatives,
            "negative_pct": f"{neg_ratio * 100:.1f}%",
        }

    # Create AI Samples
    ai_dir = FIXTURES_DIR / "ai-samples"
    for item in AI_SAMPLES:
        sample_name = item["sample"]
        text = item["text"]
        expected = item["expected"]

        # Validate word count (120 - 250 words)
        words = text.split()
        word_count = len(words)
        if not (120 <= word_count <= 250):
            raise ValueError(
                f"Sample {sample_name} word count is {word_count}, expected between 120 and 250 words"
            )

        # Validate issues count and exact verbatim quote matches
        issues = expected["issues"]
        if not (5 <= len(issues) <= 10):
            raise ValueError(
                f"Sample {sample_name} has {len(issues)} issues, expected 5 to 10"
            )

        must_detect_count = sum(1 for iss in issues if iss["must_detect"])
        if not (3 <= must_detect_count <= 5):
            raise ValueError(
                f"Sample {sample_name} has {must_detect_count} must_detect issues, expected 3 to 5"
            )

        for iss in issues:
            quote = iss["quote"]
            count = text.count(quote)
            if count != 1:
                raise ValueError(
                    f"Quote '{quote}' in {sample_name} must appear exactly once in .txt, but appeared {count} times"
                )

        txt_path = ai_dir / f"{sample_name}.txt"
        json_path = ai_dir / f"{sample_name}.expected.json"

        write_file(txt_path, text)
        write_file(json_path, dump_json_with_zwnj_escapes(expected))
        files_created += 2

    # Print summary report
    print("=" * 60)
    print("Farsi-lint Fixtures Generation Complete")
    print("=" * 60)
    print(f"Total files written: {files_created}")
    print("\nNormalizer Rule Cases Breakdown:")
    for rule, stats in rule_stats.items():
        print(
            f"  - {rule:18s}: {stats['total']:2d} cases (Pos: {stats['positive']:2d}, Neg: {stats['negative']:2d} -> {stats['negative_pct']})"
        )
    print(f"\nAI Evaluation Samples: {len(AI_SAMPLES)} pairs (.txt + .expected.json)")
    for s in AI_SAMPLES:
        word_cnt = len(s["text"].split())
        issue_cnt = len(s["expected"]["issues"])
        must_cnt = sum(1 for i in s["expected"]["issues"] if i["must_detect"])
        print(
            f"  - {s['sample']:28s}: {word_cnt:3d} words | {issue_cnt} issues ({must_cnt} must_detect)"
        )
    print("=" * 60)


if __name__ == "__main__":
    generate_all_fixtures()

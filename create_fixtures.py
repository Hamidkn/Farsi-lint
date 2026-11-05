#!/usr/bin/env python3
"""Seed the unreviewed Persian fixture corpus using only the Python 3 standard library.

Run from the repository root: python create_fixtures.py
This overwrites only the explicitly generated paths; it never deletes files.
The visible ~ marker in authored strings becomes U+200C via z().
"""

import json
import math
from pathlib import Path
import re


ZWNJ = "\u200c"
CATEGORIES = [
    "translationese", "unnatural", "grammar", "register", "collocation",
    "redundancy", "terminology", "clarity",
]
SEVERITIES = ["error", "warning", "suggestion"]


def z(text):
    """Keep invisible ZWNJs out of the source; materialize them only at runtime."""
    return text.replace("~", ZWNJ)


def p(before, after, note, options=None):
    return {
        "input": z(before), "expected": z(after), "options": options or {},
        "kind": "positive", "note": note, "reviewed": False,
    }


def n(text, note, options=None):
    return {
        "input": z(text), "expected": z(text), "options": options or {},
        "kind": "negative", "note": note, "reviewed": False,
    }


def normalizer_documents():
    rules = {}

    def add(rule, description, cases):
        for number, case in enumerate(cases, 1):
            case["id"] = "{}-{:03d}".format(rule, number)
        rules[rule] = {"rule": rule, "description_en": description, "cases": cases}

    add("arabic-letters", "Normalize Arabic letter variants only in Persian words; preserve lexical hamza.", [
        p("كتاب", "کتاب", "Arabic kaf in an ordinary Persian word"),
        p("كودک", "کودک", "Arabic kaf at the start"),
        p("بزرگي", "بزرگی", "Arabic yeh at the end"),
        p("كيک", "کیک", "Arabic kaf and yeh in the same word"),
        p("خيابان", "خیابان", "Arabic yeh inside a word"),
        p("مدرسة", "مدرسه", "Persian word ending in heh, not Arabic ta marbuta"),
        p("نقطة", "نقطه", "Ta marbuta in the Persian word for point"),
        p("شبکة", "شبکه", "Ta marbuta in the Persian word for network"),
        p("إمکان", "امکان", "Initial hamza is not retained in this Persian word"),
        p("إجرا", "اجرا", "Initial hamza in a Persian context"),
        p("أخبار", "اخبار", "Initial hamza in the Persian word for news"),
        p("أثر", "اثر", "Initial hamza in the Persian word for effect"),
        n("کتاب کودک", "Persian kaf already correct"),
        n("خیابان بزرگی", "Persian yeh already correct"),
        n("مسئله", "Do not strip a lexical hamza"),
        n("مسأله", "Preserve the accepted alternate spelling requested by the fixture contract"),
        n("رئیس", "Hamza on yeh is part of the spelling"),
        n("تأثیر", "Medial hamza on alef must remain"),
        n("مؤسسه", "Hamza on waw must remain; no blanket replacement of waw-hamza"),
        n("رؤیا", "Hamza on waw in an established Persian spelling"),
    ])

    persian = {"digits": "persian"}
    keep = {"digits": "keep"}
    add("digits", "Convert digits in Persian context only when requested; preserve technical and English spans.", [
        p("تعداد 456 نفر", "تعداد ۴۵۶ نفر", "ASCII digits in Persian prose", persian),
        p("تعداد ٤٥٦ نفر", "تعداد ۴۵۶ نفر", "Arabic-Indic digits in Persian prose", persian),
        p("رقم 0", "رقم ۰", "ASCII zero", persian),
        p("رقم ٠", "رقم ۰", "Arabic-Indic zero", persian),
        p("اعداد 1234567890", "اعداد ۱۲۳۴۵۶۷۸۹۰", "All ten ASCII digit mappings", persian),
        p("اعداد ١٢٣٤٥٦٧٨٩٠", "اعداد ۱۲۳۴۵۶۷۸۹۰", "All ten Arabic-Indic digit mappings", persian),
        p("صفحه 12 از ٣٠", "صفحه ۱۲ از ۳۰", "Mixed source digit alphabets", persian),
        p("سال 1405 است.", "سال ۱۴۰۵ است.", "Year within Persian context", persian),
        p("بخش 2 و بند ٧", "بخش ۲ و بند ۷", "Separated numeric tokens", persian),
        n("تعداد ۴۵۶ نفر", "Already Persian digits", persian),
        n("تعداد 456 نفر", "Explicit keep option suppresses conversion", keep),
        n("تعداد ٤٥٦ نفر", "Keep applies to Arabic-Indic digits too", keep),
        n("UTF8 MP3 X7", "Digits within Latin alphanumeric words", persian),
        n("https://example.invalid/v2?id=456", "URL digits are immutable", persian),
        n("نسخه v2.1 آماده است.", "Prefixed version number", persian),
        n("نسخه 3.5.0 آماده است.", "Bare three-part version number", persian),
        n('`const n = 456;`', "Inline code", persian),
        n("Released on 2026-11-05.", "ISO date in an English sentence", persian),
        n("Call +1-202-555-0123 for help.", "Reserved fictional phone number in English context", persian),
        n("user456@example.invalid", "Email local-part digits", persian),
    ])

    add("zwnj", "Join unambiguous verbal prefixes and productive suffixes; preserve lexical lookalikes.", [
        p("می روم", "می~روم", "Verbal prefix mi"),
        p("نمی دانم", "نمی~دانم", "Negative verbal prefix nemi"),
        p("می نویسم", "می~نویسم", "Mi before a joining stem"),
        p("نمی بینیم", "نمی~بینیم", "Nemi with a plural verb"),
        p("کتاب ها", "کتاب~ها", "Plural ha after a joining letter"),
        p("پنجره های اتاق", "پنجره~های اتاق", "Plural hay before ezafe"),
        p("خانه هایی بزرگ", "خانه~هایی بزرگ", "Indefinite plural hayi"),
        p("بزرگ تر", "بزرگ~تر", "Productive comparative suffix"),
        p("سخت ترین", "سخت~ترین", "Productive superlative suffix"),
        p("خسته ام", "خسته~ام", "First-person singular copula after silent heh"),
        p("خسته ای", "خسته~ای", "Second-person singular copula after silent heh"),
        p("خسته ایم", "خسته~ایم", "First-person plural copula after silent heh"),
        p("خسته اید", "خسته~اید", "Second-person plural copula after silent heh"),
        p("خسته اند", "خسته~اند", "Third-person plural copula after silent heh"),
        p("خانه ای خریدم.", "خانه~ای خریدم.", "Indefinite suffix, not ezafe"),
        n("میز و میوه", "Lexical words beginning with mi"),
        n("میهن", "Lexical prefix lookalike"),
        n("هایل", "Lexical boundary counterexample specified by the task"),
        n("ترانه و بستر", "Lexical words containing tar"),
        n("اندام", "Lexical and prefix must not be detached"),
        n("کتابی و ماهی", "Final yeh is not a detachable suffix here"),
        n("می~روم و نمی~دانم", "Correct verbal ZWNJs"),
        n("کتاب~ها و پنجره~های اتاق", "Correct plural ZWNJs"),
        n("بهتر و بیشتر", "Established joined comparative forms"),
        n("items remain unchanged", "Latin words"),
    ])

    add("zwnj-cleanup", "Remove redundant ZWNJs; preserve meaningful joining boundaries.", [
        p("متن ~فارسی~ است.", "متن فارسی است.", "ZWNJ on either side of a regular space"),
        p("می~~روم", "می~روم", "Double ZWNJ"),
        p("کتاب~~~ها", "کتاب~ها", "Triple ZWNJ"),
        p("~کتاب", "کتاب", "ZWNJ at the start of a word"),
        p("کتاب~", "کتاب", "ZWNJ at the end of a word"),
        p("ا~بر", "ابر", "Redundant ZWNJ after alef"),
        p("د~ست", "دست", "Redundant ZWNJ after dal"),
        p("ذ~هن", "ذهن", "Redundant ZWNJ after zal"),
        p("ر~نگ", "رنگ", "Redundant ZWNJ after reh"),
        p("ز~بان", "زبان", "Redundant ZWNJ after zeh"),
        p("ژ~رف", "ژرف", "Redundant ZWNJ after zheh"),
        p("و~قت", "وقت", "Redundant ZWNJ after waw"),
        n("می~روم", "Correct prefix boundary"),
        n("نمی~دانم", "Correct negative-prefix boundary"),
        n("کتاب~ها", "Correct plural boundary"),
        n("پنجره~های اتاق", "Correct heh-plural boundary"),
        n("خسته~ام", "Correct copular boundary"),
        n("خانه~ای", "Correct indefinite suffix"),
        n("بزرگ~تر", "Correct comparative boundary"),
        n("سخت~ترین", "Correct superlative boundary"),
    ])

    add("spaces", "Collapse excess horizontal spaces and remove trailing/pre-punctuation spaces without flattening lines.", [
        p("متن  فارسی", "متن فارسی", "Double space"),
        p("این   متن است.", "این متن است.", "Triple space"),
        p("سلام ", "سلام", "Trailing space at end of input"),
        p("سلام   ", "سلام", "Several trailing spaces"),
        p("سطر نخست  \nسطر دوم", "سطر نخست\nسطر دوم", "Trailing spaces on a line; keep newline"),
        p("سلام ، دوست من.", "سلام، دوست من.", "Space before comma"),
        p("تمام شد .", "تمام شد.", "Space before full stop"),
        p("آماده است ؟", "آماده است؟", "Space before question mark"),
        p("متن  نخست\n\nمتن  دوم", "متن نخست\n\nمتن دوم", "Collapse spaces while preserving paragraph break"),
        n("متن فارسی", "Single inter-word space"),
        n("سطر نخست\nسطر دوم", "Intentional line break"),
        n("بند نخست\n\nبند دوم", "Intentional paragraph break"),
        n("بند نخست\n\n\nبند دوم", "Multiple intentional blank lines"),
        n("سلام، دوست من.", "Correct punctuation spacing"),
        n("سطر نخست\nسطر دوم\n", "Terminal newline preserved"),
    ])

    add("punctuation", "Use Persian comma/semicolon/question mark in Persian prose, with context-aware spacing.", [
        p("سلام, دوست من.", "سلام، دوست من.", "Persian-context comma"),
        p("آمدم; کسی نبود.", "آمدم؛ کسی نبود.", "Persian-context semicolon"),
        p("آماده هستید?", "آماده هستید؟", "Persian-context question mark"),
        p("سلام،دوست من.", "سلام، دوست من.", "Missing space after comma"),
        p("آمدم؛کسی نبود.", "آمدم؛ کسی نبود.", "Missing space after semicolon"),
        p("آماده است؟بله.", "آماده است؟ بله.", "Missing space after question mark"),
        p("سلام ، دوست من.", "سلام، دوست من.", "Remove space before comma"),
        p("تمام شد ؛ برویم.", "تمام شد؛ برویم.", "Remove space before semicolon"),
        p("آماده است ?بله.", "آماده است؟ بله.", "Conversion plus spacing"),
        n("سلام، دوست من؛ آماده هستید؟", "Correct Persian marks"),
        n("متن انگلیسی: Hello, friend; are you ready?", "Whole embedded English sentence, including its punctuation"),
        n("عدد ۳٫۵ ثبت شد.", "Persian decimal separator"),
        n("The value is 3.5, not 4.0.", "English decimal numbers and punctuation"),
        n('`if (x) { f(a, b); }`', "Code punctuation"),
        n("https://example.invalid/search?q=1;mode=2", "Question mark and semicolon inside a URL"),
    ])

    add("quotes", "Convert paired straight/curly quotes around Persian prose, preserving English and structured data.", [
        p('او گفت: "سلام".', "او گفت: «سلام».", "Straight quotation marks"),
        p("او گفت: “سلام”.", "او گفت: «سلام».", "Curly quotation marks"),
        p('"کتاب" را بخوان.', "«کتاب» را بخوان.", "Quoted object at sentence start"),
        p("“پایان”", "«پایان»", "Standalone curly quotation"),
        p('عنوان: "راهنمای سفر"', "عنوان: «راهنمای سفر»", "Multiword title"),
        p('او نوشت: "می~آیم".', "او نوشت: «می~آیم».", "Retain an existing ZWNJ"),
        p('"بله" یا "نه"؟', "«بله» یا «نه»؟", "Two independent quoted spans"),
        p('او گفت: " سلام ".', "او گفت: «سلام».", "Trim spaces just inside quotes"),
        p("عنوان: “خانهٔ روشن”", "عنوان: «خانهٔ روشن»", "Keep combining hamza inside converted quotes"),
        n("او گفت: «سلام».", "Correct guillemets"),
        n('She said "hello".', "English straight quotes"),
        n("She said “hello”.", "English curly quotes"),
        n('`print("سلام")`', "Code containing Persian text"),
        n('{"message": "سلام"}', "JSON-like object, including its Persian value"),
        n('متن انگلیسی: Say "hello" now.', "English quotation embedded in Persian prose"),
    ])

    add("brackets-spacing", "No inner spaces and normal prose spacing outside parentheses/brackets/guillemets; preserve code and Markdown.", [
        p("این ( متن ) درست است.", "این (متن) درست است.", "Parentheses: trim both inner spaces"),
        p("این [ متن ] درست است.", "این [متن] درست است.", "Square brackets: trim inner spaces"),
        p("این « متن » درست است.", "این «متن» درست است.", "Guillemets: trim inner spaces"),
        p("این(متن) درست است.", "این (متن) درست است.", "Missing outer space before parentheses"),
        p("این (متن)درست است.", "این (متن) درست است.", "Missing outer space after parentheses"),
        p("این[متن] درست است.", "این [متن] درست است.", "Missing outer space before square brackets"),
        p("این [متن]درست است.", "این [متن] درست است.", "Missing outer space after square brackets"),
        p("او «سلام»گفت.", "او «سلام» گفت.", "Missing outer space after closing guillemet"),
        p("او«سلام» گفت.", "او «سلام» گفت.", "Missing outer space before opening guillemet"),
        n("این (متن) درست است.", "Correct parentheses"),
        n("این [متن] درست است.", "Correct square brackets"),
        n("او «سلام» گفت.", "Correct guillemets"),
        n("او گفت (بله).", "No space between closing bracket and full stop"),
        n("foo(x)", "Bare function call is a technical span"),
        n("[راهنما](https://example.invalid/help)", "Markdown link syntax is immutable"),
    ])

    add("ellipsis", "Replace prose three-dot sequences with U+2026, preserving technical sequences.", [
        p("هنوز منتظرم...", "هنوز منتظرم…", "Trailing prose ellipsis"),
        p("نمی~دانم... شاید فردا.", "نمی~دانم… شاید فردا.", "Medial prose ellipsis"),
        p("... و داستان ادامه دارد.", "… و داستان ادامه دارد.", "Leading ellipsis"),
        p("گفت: «شاید...»", "گفت: «شاید…»", "Ellipsis before closing guillemet"),
        p("(ادامه دارد...)", "(ادامه دارد…)", "Ellipsis inside parentheses"),
        p("آب، نان و ...", "آب، نان و …", "Open-ended list"),
        p("صبر کن... باز هم صبر کن...", "صبر کن… باز هم صبر کن…", "Two ellipses"),
        p("بند نخست...\nبند دوم", "بند نخست…\nبند دوم", "Keep line break after ellipsis"),
        p("بند نخست...\n\nبند دوم", "بند نخست…\n\nبند دوم", "Keep paragraph break after ellipsis"),
        n("هنوز منتظرم…", "Already a Unicode ellipsis"),
        n("تمام شد.", "A single full stop"),
        n("`const copy = [...items];`", "Spread operator in inline code"),
        n("```python\nvalue = ...\n```", "Ellipsis literal in fenced code"),
        n("نسخه v1.0...v2.0 پشتیبانی می~شود.", "Technical version range is not prose ellipsis"),
        n("https://example.invalid/path.../file", "Three dots in URL path"),
    ])

    add("kashida", "Remove decorative U+0640 tatweel without changing otherwise correct text.", [
        p("سـلام", "سلام", "Single tatweel"),
        p("کتــاب", "کتاب", "Two consecutive tatweels"),
        p("خــانه", "خانه", "Tatweel inside a noun"),
        p("مـتـن", "متن", "Separated tatweels"),
        p("فـارسی", "فارسی", "Tatweel inside a language adjective"),
        p("بـله", "بله", "Tatweel in a short word"),
        p("نـه", "نه", "Tatweel before heh"),
        p("کـتاب~ها", "کتاب~ها", "Retain a valid ZWNJ while removing tatweel"),
        p("سـلام، خـوش آمدید.", "سلام، خوش آمدید.", "Tatweels in two words"),
        n("سلام", "Undecorated word"),
        n("کتاب~ها", "ZWNJ is not tatweel"),
        n("خانهٔ من", "Combining hamza is not tatweel"),
        n("می~روم", "Verbal prefix boundary preserved"),
        n("متن فارسی.", "Ordinary sentence"),
        n("[متن]", "Punctuation preserved"),
    ])

    hamza = {"hehYeStyle": "hamza"}
    ye = {"hehYeStyle": "zwnj"}
    add("heh-ye", "Render ezafe after silent heh in the explicitly selected style; do not confuse it with indefinite/copular suffixes.", [
        p("خانه ی من", "خانهٔ من", "Separated ezafe yeh, hamza style", hamza),
        p("خانه ی من", "خانه~ی من", "Separated ezafe yeh, ZWNJ style", ye),
        p("نامه ی شما", "نامهٔ شما", "Letter with ezafe, hamza style", hamza),
        p("نامه ی شما", "نامه~ی شما", "Letter with ezafe, ZWNJ style", ye),
        p("پنجره ی اتاق", "پنجرهٔ اتاق", "Window with ezafe, hamza style", hamza),
        p("پنجره ی اتاق", "پنجره~ی اتاق", "Window with ezafe, ZWNJ style", ye),
        p("خانه~ی من", "خانهٔ من", "Convert the alternate ezafe style when explicitly selected", hamza),
        p("خانهٔ من", "خانه~ی من", "Convert hamza style to explicitly selected ZWNJ style", ye),
        p("درباره ی کتاب", "دربارهٔ کتاب", "Ezafe after a heh-final preposition", hamza),
        p("درباره ی کتاب", "درباره~ی کتاب", "Same preposition with alternate configured style", ye),
        n("خانهٔ من", "Already in requested hamza style", hamza),
        n("خانه~ی من", "Already in requested ZWNJ style", ye),
        n("خانه~ای خریدم.", "Indefinite suffix is not ezafe", hamza),
        n("خانه~ای خریدم.", "Indefinite suffix under alternate style", ye),
        n("خسته~ای.", "Copular suffix is not ezafe", hamza),
        n("نامه~ای رسید.", "Indefinite letter", ye),
        n("دریا آرام است.", "Yeh within a lexical stem", hamza),
        n("ماهی در آب است.", "Final yeh unrelated to silent-heh ezafe", ye),
        n("راه من", "Pronounced final heh does not take this transformation", hamza),
        n("کوه بلند", "Pronounced final heh", ye),
    ])

    add("protected-spans", "All rules enabled: fix surrounding Persian but keep every protected span byte-identical.", [
        p("مي~روم به https://example.invalid/كتاب?q=123;mode=2", "می~روم به https://example.invalid/كتاب?q=123;mode=2", "Persian outside URL; Arabic kaf and punctuation inside preserved"),
        p("نشانی user123@example.invalid را مي~بینم.", "نشانی user123@example.invalid را می~بینم.", "Email preserved"),
        p('مي~نویسم: `const s = "كتاب 12...";`', 'می~نویسم: `const s = "كتاب 12...";`', "Inline code with several apparent normalization triggers"),
        p('كد زیر:\n```js\nconst s = "مي روم 12...";\n```', 'کد زیر:\n```js\nconst s = "مي روم 12...";\n```', "Fenced code containing malformed Persian"),
        p("كتاب برای @reader_123 است.", "کتاب برای @reader_123 است.", "Mention boundary preserved"),
        p("كتاب با #كتاب123 ثبت شد.", "کتاب با #كتاب123 ثبت شد.", "Persian hashtag letters and digits preserved"),
        p("اين فایل UTF8 است.", "این فایل UTF8 است.", "Latin alphanumeric token preserved"),
        p("نسخه v2.1 را مي~بینم.", "نسخه v2.1 را می~بینم.", "Version number next to Persian correction"),
        p("اين متن: Hello, friend; ready?", "این متن: Hello, friend; ready?", "Whole Latin-script run including punctuation preserved"),
        p('اين داده: {"key": "كتاب 12"}', 'این داده: {"key": "كتاب 12"}', "JSON-like span preserved even with Persian content"),
        n("https://example.invalid/كتاب?q=123;mode=2", "URL only"),
        n("user123@example.invalid", "Email only"),
        n('`const s = "مي روم 123...";`', "Inline code only"),
        n('```txt\nكتاب ها 123...\n```', "Fenced code only"),
        n("@reader_123", "Mention only"),
        n("#كتاب123", "Persian hashtag only"),
        n("Hello, friend; ready?", "English sentence with punctuation"),
        n("متن با نسخه 3.5.0 سازگار است.", "Bare technical version"),
        n('داده: {"message": "خانه ي 123"}', "Structured data with Persian-looking errors"),
        n("[كتاب 123](https://example.invalid/help?q=1)", "Entire Markdown link is a protected technical span"),
    ])

    add("combined", "Paragraph-level integration expectations, including protected spans and already-correct paragraphs.", [
        p("اين كتاب ها را مي خوانم, اما 2 صفحه مانده است...", "این کتاب~ها را می~خوانم، اما ۲ صفحه مانده است…", "Five rule families: letters, affixes, punctuation, digits, ellipsis"),
        p('او گفت: "خانه ی من". پنجره ها  باز است ؟', "او گفت: «خانهٔ من». پنجره~ها باز است؟", "Five families: quotes, ezafe, affixes, spaces, punctuation", hamza),
        p("اين [ متن ] را مي خوانم. نسخه v2.1 در https://example.invalid/كتاب?id=12 ثبت شده است...", "این [متن] را می~خوانم. نسخه v2.1 در https://example.invalid/كتاب?id=12 ثبت شده است…", "Four families plus immutable URL/version"),
        p("نـامه ی شما رسيد; پاسخ را مي نويسم.", "نامهٔ شما رسید؛ پاسخ را می~نویسم.", "Five families: tatweel, ezafe, letters, punctuation, affixes", hamza),
        p("گزارش  ٤٥٦ آماده است. لطفاً ( بخش نخست ) را بخوانيد, سپس نظر بدهيد.", "گزارش ۴۵۶ آماده است. لطفاً (بخش نخست) را بخوانید، سپس نظر بدهید.", "Five families: spaces, digits, brackets, letters, punctuation"),
        p('اين خانه ی من است. او گفت: “مي آيم”... كد `x = 12;` ثابت است.', 'این خانه~ی من است. او گفت: «می~آیم»… کد `x = 12;` ثابت است.', "Five families with configured ezafe and protected inline code", ye),
        n("من کتاب~ها را می~خوانم. پنجرهٔ اتاق باز است.", "Correct two-sentence Persian paragraph", hamza),
        n("نسخه v2.1 آماده است. راهنما در https://example.invalid/help?id=12 قرار دارد.", "Correct paragraph containing protected spans"),
        n("او گفت: «خانه~ای خریده~ام». سپس نامه را خواند.", "Correct quoted indefinite and copular suffixes"),
        n("بند نخست روشن است.\n\nبند دوم نیز روشن است؛ تغییری لازم نیست.", "Correct paragraphs retain their separation"),
    ])
    return rules


def issue(quote, category, severity, suggestion, explanation, must_detect):
    return {
        "quote": z(quote), "category": category, "severity": severity,
        "suggestion": z(suggestion), "explanation_fa": z(explanation),
        "must_detect": must_detect,
    }


def ai_documents():
    """Original synthetic prose; deliberately bad style, with clean orthography."""
    samples = {}

    def add(name, paragraphs, issues):
        text = z("\n\n".join(paragraphs)) + "\n"
        samples[name] = (text, {
            "sample": name, "source": "synthetic", "issues": issues, "reviewed": False,
        })

    add("01-formal-email", [
        "با سلام و احترام، برای درخواست یک جلسهٔ کوتاه دربارهٔ برنامهٔ فصل آینده خدمت شما می~نویسم. امیدوارم این پیام شما را خوب پیدا کند. در پایان روز، هدف ما رسیدن به توافقی روشن دربارهٔ زمان تحویل است و می~خواهم مطمئن شوم که همه روی یک صفحه هستیم. همچنین لازم است دربارهٔ تقسیم وظایف گفت~وگو کنیم، در حالی که گزارش اولیه توسط گروه برنامه~ریزی تهیه شده است و هنوز چند پرسش باز دارد.",
        "لطفاً پیشنهاد زمان جلسه را بررسی کنید توسط شما و نتیجه را تا فردا بفرستید. من برای هماهنگی تقویم آمادگی دارم و همچنین می~توانم فهرست موضوعات را پیش از جلسه ارسال کنم. پیوست را به همکاران فرستادم را تا فرصت کافی برای مطالعه داشته باشند. اگر زمان پیشنهادی مناسب نیست، خواهشمندم ساعت دیگری اعلام فرمایید. همچنین حضور مسئول پشتیبانی به ما کمک خواهد کرد که تصمیم~های عملی بگیریم. با تشکر و سپاس و قدردانی از وقتی که برای بررسی این درخواست اختصاص می~دهید، منتظر پاسخ شما هستم.",
    ], [
        issue("امیدوارم این پیام شما را خوب پیدا کند", "translationese", "warning", "امیدوارم حالتان خوب باشد", "این عبارت ترجمهٔ لفظی یک تعارف انگلیسی است.", True),
        issue("در پایان روز", "translationese", "warning", "در نهایت", "در این جمله منظور نتیجهٔ نهایی است، نه پایان زمان روز.", True),
        issue("همه روی یک صفحه هستیم", "translationese", "warning", "همه برداشت مشترکی داریم", "این تعبیر انگلیسی در این بافت فارسی طبیعی نیست.", True),
        issue("لطفاً پیشنهاد زمان جلسه را بررسی کنید توسط شما", "grammar", "error", "لطفاً پیشنهاد زمان جلسه را بررسی کنید", "عبارت پایانی در ساخت فعل امری جایگاه دستوری ندارد.", True),
        issue("پیوست را به همکاران فرستادم را", "grammar", "error", "پیوست را به همکاران فرستادم", "نشانهٔ مفعول پس از فعل تکرار شده است.", True),
        issue("همچنین لازم است دربارهٔ تقسیم وظایف گفت~وگو کنیم، در حالی که گزارش اولیه توسط گروه برنامه~ریزی تهیه شده است", "unnatural", "suggestion", "لازم است دربارهٔ تقسیم وظایف گفت~وگو کنیم؛ گروه برنامه~ریزی گزارش اولیه را تهیه کرده است", "رابطهٔ تقابلی روشنی وجود ندارد و ساخت فعال روان~تر است.", False),
        issue("با تشکر و سپاس و قدردانی", "redundancy", "suggestion", "با سپاس", "چند واژهٔ هم~معنا بدون افزودن اطلاعات تکرار شده~اند.", False),
    ])

    add("02-linkedin-post", [
        "خوشحالم اعلام کنم که پس از چند ماه تلاش، مسئولیت هماهنگی یک طرح تازه را پذیرفته~ام. این موفقیت یک بازی را تغییر می~دهد برای مسیر شغلی من. در این سفر یادگیری، بارها از منطقهٔ راحتی خود بیرون قدم گذاشتم و یاد گرفتم که چگونه تصمیم بسازم. همچنین همکاری با گروهی صبور و دقیق باعث شد مسائل دشوار را از زاویه~های تازه ببینم، در حالی که هر روز فرصتی برای رشد و توسعهٔ فردی و شخصی فراهم بود.",
        "این دستاورد توسط همکاران همراه من ممکن شده است و نقش هر یک از آنان برایم ارزش دارد. همچنین می~خواهم از کسانی که بازخورد روشن دادند قدردانی کنم. از این پس مدیریت همان طرح را بر عهده دارم؛ در برنامهٔ داخلی، این مسئولیت هدایت پروژه نامیده می~شود و در گزارش~های بعدی دوباره از واژهٔ طرح استفاده خواهم کرد. همچنین هدفم این است که تجربه~های کاربردی را با دیگران به اشتراک بگذارم. مسیر تازه هنوز پرسش~های فراوان دارد، اما نسبت به ادامهٔ کار احساس هیجان~زده دارم و برای شنیدن پیشنهادهای شما آماده~ام.",
    ], [
        issue("این موفقیت یک بازی را تغییر می~دهد برای مسیر شغلی من", "translationese", "warning", "این موفقیت نقطهٔ عطفی در مسیر شغلی من است", "ترجمهٔ لفظی اصطلاح انگلیسی و ترتیب اجزای جمله نامأنوس است.", True),
        issue("از منطقهٔ راحتی خود بیرون قدم گذاشتم", "translationese", "warning", "کارهایی فراتر از تجربه~های معمول خود انجام دادم", "ترکیب مکانی ترجمهٔ تحت~اللفظی یک اصطلاح انگلیسی است.", False),
        issue("تصمیم بسازم", "collocation", "error", "تصمیم بگیرم", "در فارسی تصمیم را می~گیرند، نه اینکه آن را بسازند.", True),
        issue("رشد و توسعهٔ فردی و شخصی", "redundancy", "suggestion", "رشد فردی", "صفت~ها و اسم~های نزدیک به هم بی~دلیل تکرار شده~اند.", False),
        issue("این دستاورد توسط همکاران همراه من ممکن شده است", "unnatural", "suggestion", "همراهی همکارانم این دستاورد را ممکن کرده است", "ساخت فعال نقش همکاران را روشن~تر بیان می~کند.", False),
        issue("این مسئولیت هدایت پروژه نامیده می~شود", "terminology", "suggestion", "این مسئولیت هدایت طرح نامیده می~شود", "برای اشاره به همان کار بهتر است اصطلاح طرح یکدست بماند.", False),
        issue("احساس هیجان~زده دارم", "collocation", "error", "احساس هیجان دارم", "پس از احساس در این ساخت به اسم نیاز است.", True),
    ])

    add("03-translated-tech-article", [
        "در یک سامانهٔ پردازش درخواست، گلوگاه همیشه جایی نیست که نخست به نظر می~رسد. برای نمونه، افزودن پردازندهٔ بیشتر می~تواند زمان پاسخ را کاهش دهد، در حالی که صف پیام هنوز با سرعت ثابتی پر می~شود. در این نقطه باید یک نگاه نزدیک بگیریم به مسیر داده و ببینیم کدام مرحله هزینهٔ اصلی را ایجاد می~کند. همچنین ابزار پایش به ما دیدپذیری می~دهد به رفتار سامانه و کمک می~کند علت تأخیر را پیدا کنیم.",
        "در این نوشته، بافر بخشی از حافظه است که داده را پیش از پردازش نگه می~دارد. در مرحلهٔ بعد، ظرفیت میانگیر را تنظیم می~کنیم تا داده~های ورودی فضای کافی داشته باشند. همچنین باید در ذهن نگه داشت که خطاها توسط سرویس ثبت می~شوند و هشدارها توسط سرویس ارسال می~شوند. برای کاهش زمان پاسخ، درخواست~ها را پردازش می~کند سامانه به ترتیب ورود. این روش یک اندازه برای همه مناسب است نیست و لازم است شرایط هر برنامه جداگانه بررسی شود. در نهایت، معیار خوب باید به یک تصمیم عملی منجر شود، در حالی که انباشت عددها به تنهایی مسئله~ای را حل نمی~کند.",
    ], [
        issue("یک نگاه نزدیک بگیریم به مسیر داده", "translationese", "warning", "مسیر داده را دقیق بررسی کنیم", "این عبارت ساخت و ترتیب واژه~های یک تعبیر انگلیسی را تقلید می~کند.", True),
        issue("دیدپذیری می~دهد به رفتار سامانه", "unnatural", "warning", "امکان مشاهدهٔ رفتار سامانه را فراهم می~کند", "همایندی و ترتیب اجزای این عبارت در فارسی طبیعی نیست.", True),
        issue("ظرفیت میانگیر را تنظیم می~کنیم", "terminology", "warning", "ظرفیت بافر را تنظیم می~کنیم", "متن برای یک مفهوم واحد دو اصطلاح را بی~توضیح جابه~جا می~کند.", False),
        issue("باید در ذهن نگه داشت", "translationese", "suggestion", "باید در نظر داشت", "این ترکیب در این بافت گرته~برداری لفظی است.", False),
        issue("خطاها توسط سرویس ثبت می~شوند و هشدارها توسط سرویس ارسال می~شوند", "unnatural", "suggestion", "سرویس خطاها را ثبت و هشدارها را ارسال می~کند", "تکرار ساخت مجهول جمله را سنگین کرده است.", False),
        issue("درخواست~ها را پردازش می~کند سامانه به ترتیب ورود", "grammar", "warning", "سامانه درخواست~ها را به ترتیب ورود پردازش می~کند", "ترتیب اجزای جمله در نثر توضیحی بی~دلیل نامعمول شده است.", False),
        issue("این روش یک اندازه برای همه مناسب است نیست", "translationese", "error", "این روش برای همهٔ شرایط مناسب نیست", "ترجمهٔ لفظی اصطلاح انگلیسی ساخت جمله را نیز مختل کرده است.", True),
    ])

    add("04-customer-support", [
        "کاربر گرامی، از اینکه دربارهٔ تأخیر سفارش با ما تماس گرفتید سپاسگزاریم. ما درد شما را احساس می~کنیم و می~دانیم که انتظار طولانی می~تواند برنامهٔ روزانه را به هم بزند. درخواست شما توسط گروه پشتیبانی دریافت شده است و بررسی آن توسط گروه ارسال انجام خواهد شد. همچنین شمارهٔ پیگیری در حساب شما قرار دارد، در حالی که وضعیت بسته هنوز نیازمند بررسی بیشتر است. برای حرکت به جلو، لطفاً تصویر رسید را در پاسخ همین پیام بفرستید.",
        "ما تلاش می~کنیم تا در اسرع وقت هرچه زودتر پاسخ روشنی ارائه دهیم. اگر بسته تا فردا نرسید، وجه سفارش به کیف پول شما برگردانده خواهد شد. برای بررسی مبلغ، صفحهٔ حساب را باز کنید و موجودی حساب را بخوانید. هنگام برداشت نیز گزینهٔ اعتبار مشتری را انتخاب کنید. شما می~توانید این وجه را برداشت کنید یا برای خرید بعدی نگه دارید. همچنین ما مسئولیت تأخیر را به دوش می~گیریم و امیدواریم تجربهٔ بعدی بهتر باشد. برای ثبت پیگیری نهایی، لطفاً رسید را ارسال نمایید و بعدش یه پیام بده که بدونیم فرستادی. از شکیبایی شما سپاسگزاریم.",
    ], [
        issue("ما درد شما را احساس می~کنیم", "translationese", "warning", "ناراحتی شما را درک می~کنیم", "تعبیر لفظی درد در پاسخ به تأخیر سفارش نامتناسب است.", True),
        issue("درخواست شما توسط گروه پشتیبانی دریافت شده است و بررسی آن توسط گروه ارسال انجام خواهد شد", "unnatural", "suggestion", "گروه پشتیبانی درخواست شما را دریافت کرده است و گروه ارسال آن را بررسی خواهد کرد", "دو ساخت مجهول پیاپی پاسخ را اداری و سنگین کرده~اند.", False),
        issue("برای حرکت به جلو", "translationese", "suggestion", "برای ادامهٔ بررسی", "این عبارت ترجمهٔ لفظی و مبهمی برای مرحلهٔ بعدی رسیدگی است.", False),
        issue("در اسرع وقت هرچه زودتر", "redundancy", "warning", "در اسرع وقت", "هر دو عبارت یک معنا را تکرار می~کنند.", True),
        issue("گزینهٔ اعتبار مشتری را انتخاب کنید", "terminology", "warning", "گزینهٔ موجودی حساب را انتخاب کنید", "نام واحد برای موجودی قابل برداشت از سردرگمی جلوگیری می~کند.", True),
        issue("ما مسئولیت تأخیر را به دوش می~گیریم", "collocation", "warning", "ما مسئولیت تأخیر را می~پذیریم", "فعل پذیرفتن با مسئولیت در این پاسخ رسمی طبیعی~تر است.", False),
        issue("بعدش یه پیام بده که بدونیم فرستادی", "register", "error", "سپس ارسال رسید را با پیامی تأیید کنید", "عبارت محاوره~ای با لحن رسمی پاسخ پشتیبانی هماهنگ نیست.", True),
    ])

    add("05-product-description", [
        "این چراغ رومیزی برای مطالعه و کار روزانه طراحی شده است و بدنه~ای سبک با پایهٔ قابل تنظیم دارد. طراحی آن تجربهٔ شما را به سطح بعدی می~برد و اجازه می~دهد کار بیشتری را انجام دهید با تلاش کمتر. شدت نور در سه حالت تغییر می~کند و دکمهٔ روی پایه دسترسی آسانی دارد. همچنین نور چراغ برای کتاب خواندن مناسب است، در حالی که زاویهٔ تابش را می~توان متناسب با جای نشستن تنظیم کرد.",
        "یکی از ویژگی~های مهم، مصرف بهینهٔ انرژی است. این دستگاه مصرف انرژی را پس~انداز می~کند و می~تواند ساعت~های طولانی روشن بماند. در بخش مشخصات، توان مصرفی هشت وات نوشته شده است، اما در همین توضیح توان چراغ با عنوان قدرت نوری معرفی می~شود؛ این دو عنوان برای همان عدد به کار رفته~اند. همچنین پایه فضای کمی اشغال می~کند و برای میز کوچک مناسب است. این محصول یک انتخاب منحصربه~فرد و بی~نظیر و یگانه برای هر کاربر است. اگر دنبال چراغی ساده هستید، این مدل نیاز شما را انجام می~دهد و همراه مناسبی برای مطالعه خواهد بود.",
    ], [
        issue("تجربهٔ شما را به سطح بعدی می~برد", "translationese", "warning", "مطالعه و کار روزانه را آسان~تر می~کند", "این شعار ترجمهٔ لفظی است و مزیت مشخصی را بیان نمی~کند.", True),
        issue("کار بیشتری را انجام دهید با تلاش کمتر", "unnatural", "warning", "با تلاش کمتر کار بیشتری انجام دهید", "جای عبارت قیدی از ترتیب معمول فارسی فاصله گرفته است.", False),
        issue("این دستگاه مصرف انرژی را پس~انداز می~کند", "collocation", "error", "این دستگاه انرژی کمتری مصرف می~کند", "مصرف را پس~انداز نمی~کنند.", True),
        issue("توان چراغ با عنوان قدرت نوری معرفی می~شود", "terminology", "error", "همان مقدار با عنوان توان مصرفی معرفی می~شود", "توان مصرفی و کمیت مربوط به نور دو مفهوم یکسان نیستند.", True),
        issue("این دو عنوان برای همان عدد به کار رفته~اند", "clarity", "warning", "عدد هشت وات فقط توان مصرفی را نشان می~دهد", "توضیح باید روشن کند که عدد مذکور دربارهٔ مصرف برق است.", False),
        issue("منحصربه~فرد و بی~نظیر و یگانه", "redundancy", "suggestion", "مناسب", "چند صفت نزدیک به هم بدون دلیل یا شاهد تکرار شده~اند.", False),
        issue("نیاز شما را انجام می~دهد", "collocation", "error", "نیاز شما را برآورده می~کند", "فعل مناسب برای نیاز در این بافت برآورده کردن است.", True),
    ])

    add("06-mixed-register", [
        "همکاران گرامی، به اطلاع می~رساند که نشست بررسی برنامه روز سه~شنبه برگزار خواهد شد. خواهشمند است گزارش هر بخش را تا فردا ارسال فرمایید تا فرصت مطالعه فراهم باشد. بچه~ها، اگه وقت کردین یه نگاه هم به جدول بندازین. هدف جلسه این است که دربارهٔ اولویت~ها به نتیجه برسیم و مسئول هر کار مشخص شود. همچنین قرار است زمان تحویل را بررسی کنیم، در حالی که چند پیشنهاد تازه هم از سوی گروه دریافت شده است.",
        "لطفاً حضور خود را به دبیر جلسه اعلام نمایید و اگه نمی~رسین، زودتر خبر بدین. گزارش نهایی توسط مسئول هماهنگی تهیه خواهد شد و نسخهٔ آن در پوشهٔ مشترک قرار خواهد گرفت. این کار به ما کمک می~کند که یه تصمیم درست~وحسابی بگیریم و از دوباره~کاری جلوگیری نماییم. در بخش جمع~بندی، هر گروه باید یک پیشنهاد عملی ارائه دهد. مراتب جهت استحضار ایفاد می~گردد؛ خلاصه دیگه حواستون باشه جا نمونین. از همکاری شما صمیمانه تشکر می~کنم و امیدوارم این نشست بتواند برای همه نتیجه~ای کاربردی و مفید و سودمند داشته باشد.",
    ], [
        issue("بچه~ها، اگه وقت کردین یه نگاه هم به جدول بندازین", "register", "error", "همکاران، لطفاً در صورت امکان جدول را نیز بررسی کنید", "خطاب و فعل~های محاوره~ای با آغاز رسمی متن ناسازگارند.", True),
        issue("اگه نمی~رسین، زودتر خبر بدین", "register", "error", "اگر امکان حضور ندارید، زودتر اطلاع دهید", "جمله ناگهان از لحن رسمی به محاوره تغییر می~کند.", True),
        issue("یه تصمیم درست~وحسابی بگیریم", "register", "warning", "تصمیم مناسبی بگیریم", "واژه~های محاوره~ای در کنار فعل رسمی جمله یکدست نیستند.", True),
        issue("مراتب جهت استحضار ایفاد می~گردد", "unnatural", "suggestion", "این اطلاعات برای آگاهی شما ارسال می~شود", "عبارت اداری سنگین برای یک اطلاعیهٔ داخلی ضروری نیست.", False),
        issue("خلاصه دیگه حواستون باشه جا نمونین", "register", "error", "لطفاً زمان جلسه را به خاطر بسپارید", "این عبارت پس از جملهٔ بسیار رسمی تغییر لحن آشکاری دارد.", True),
        issue("گزارش نهایی توسط مسئول هماهنگی تهیه خواهد شد", "unnatural", "suggestion", "مسئول هماهنگی گزارش نهایی را تهیه خواهد کرد", "ساخت فعال در این اطلاعیه کوتاه~تر و روشن~تر است.", False),
        issue("کاربردی و مفید و سودمند", "redundancy", "suggestion", "کاربردی", "این صفت~های نزدیک به هم اطلاعات تازه~ای اضافه نمی~کنند.", False),
    ])
    return samples


def schemas(rule_names):
    normalizer = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Persian normalizer fixture file",
        "type": "object", "additionalProperties": False,
        "required": ["rule", "description_en", "cases"],
        "properties": {
            "rule": {"enum": list(rule_names)},
            "description_en": {"type": "string", "minLength": 1},
            "cases": {
                "type": "array", "minItems": 10, "maxItems": 25,
                "items": {"$ref": "#/$defs/case"},
            },
        },
        "$defs": {
            "case": {
                "type": "object", "additionalProperties": False,
                "required": ["id", "input", "expected", "options", "kind", "note", "reviewed"],
                "properties": {
                    "id": {"type": "string", "pattern": r"^[a-z-]+-\d{3}$"},
                    "input": {"type": "string"}, "expected": {"type": "string"},
                    "options": {
                        "type": "object", "additionalProperties": False,
                        "properties": {
                            "digits": {"enum": ["persian", "keep"]},
                            "hehYeStyle": {"enum": ["hamza", "zwnj"]},
                        },
                    },
                    "kind": {"enum": ["positive", "negative"]},
                    "note": {"type": "string", "minLength": 1},
                    "reviewed": {"type": "boolean"},
                },
            },
        },
        "allOf": [
            {
                "if": {"properties": {"rule": {"const": "combined"}}},
                "then": {"properties": {"cases": {"minItems": 10, "maxItems": 10}}},
                "else": {"properties": {"cases": {"minItems": 15, "maxItems": 25}}},
            },
        ],
    }
    # JSON Schema cannot compare input with expected or enforce unique IDs;
    # validate() checks those semantic invariants before writing any files.
    for count in [10] + list(range(15, 26)):
        normalizer["allOf"].append({
            "if": {"properties": {"cases": {"minItems": count, "maxItems": count}}},
            "then": {"properties": {"cases": {
                "contains": {"properties": {"kind": {"const": "negative"}}, "required": ["kind"]},
                "minContains": math.ceil(count * 0.4),
            }}},
        })
    ai = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Synthetic Persian LLM-review expectations",
        "type": "object", "additionalProperties": False,
        "required": ["sample", "source", "issues", "reviewed"],
        "properties": {
            "sample": {"type": "string", "pattern": r"^0[1-6]-[a-z]+(?:-[a-z]+)*$"},
            "source": {"const": "synthetic"},
            "reviewed": {"type": "boolean"},
            "issues": {
                "type": "array", "minItems": 5, "maxItems": 10,
                "contains": {"properties": {"must_detect": {"const": True}}, "required": ["must_detect"]},
                "minContains": 3, "maxContains": 5,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["quote", "category", "severity", "suggestion", "explanation_fa", "must_detect"],
                    "properties": {
                        "quote": {"type": "string", "minLength": 1},
                        "category": {"enum": CATEGORIES},
                        "severity": {"enum": SEVERITIES},
                        "suggestion": {"type": "string"},
                        "explanation_fa": {"type": "string", "minLength": 1},
                        "must_detect": {"type": "boolean"},
                    },
                },
            },
        },
    }
    return normalizer, ai


def validate(rules, samples):
    """Check corpus invariants independently of the existing normalizer behavior."""
    identifiers = set()
    for rule, document in rules.items():
        cases = document["cases"]
        assert len(cases) == 10 if rule == "combined" else 15 <= len(cases) <= 25, rule
        assert sum(c["kind"] == "negative" for c in cases) * 5 >= len(cases) * 2, rule
        for case in cases:
            identifier = case["id"]
            assert re.fullmatch(r"[a-z-]+-\d{3}", identifier), identifier
            assert identifier.startswith(rule + "-"), identifier
            assert identifier not in identifiers, identifier
            identifiers.add(identifier)
            assert case["reviewed"] is False, identifier
            assert (case["input"] != case["expected"]) == (case["kind"] == "positive"), identifier
            assert set(case["options"]) <= {"digits", "hehYeStyle"}, identifier
            assert case["options"].get("digits", "persian") in {"persian", "keep"}, identifier
            assert case["options"].get("hehYeStyle", "hamza") in {"hamza", "zwnj"}, identifier
            assert "\r" not in case["input"] + case["expected"], identifier
    assert len(samples) == 6
    for name, (text, expected) in samples.items():
        count = len(text.split())  # ZWNJ-joined forms count as one word.
        assert 120 <= count <= 250, (name, "word count", count)
        assert expected["reviewed"] is False and expected["source"] == "synthetic", name
        assert expected["sample"] == name, name
        issues = expected["issues"]
        assert 5 <= len(issues) <= 10, name
        assert 3 <= sum(i["must_detect"] for i in issues) <= 5, name
        assert not re.search(r"[يكـ0-9٠-٩]", text), (name, "local orthography trigger")
        assert not re.search(r"(?<![\w\u200c])(?:ن?می) +| +(?:ها|های|هایی|ام|ای|ایم|اید|اند)\b|ه +ی\b", text), (name, "unjoined affix")
        assert not re.search(ZWNJ + r"{2,}|\s" + ZWNJ + "|" + ZWNJ + r"\s", text), (name, "malformed ZWNJ")
        quotes = set()
        for item in issues:
            quote = item["quote"]
            assert quote and text.count(quote) == 1, (name, "quote must occur exactly once", quote)
            assert quote not in quotes, (name, quote)
            quotes.add(quote)
            assert item["category"] in CATEGORIES and item["severity"] in SEVERITIES, name
            assert type(item["must_detect"]) is bool, name
            assert item["suggestion"] != quote and item["explanation_fa"], name
            assert "\n" not in item["explanation_fa"], name


CLEAN_README = z("""# Human-written clean corpus

This directory contains instructions only until a human supplies reviewed text.
Add only human-written, professionally edited Persian text. Never add AI-generated
text, including a supposedly corrected or polished AI draft. Every text file must
produce zero issues from the local normalization layer.

Suggested sources are the maintainer's own carefully edited writing, or featured
Persian Wikipedia articles (CC BY-SA 4.0). Verify the particular article's license
and provenance first: being published on Wikipedia alone does not prove human
authorship. Record its article URL, revision, author attribution and license in
the sources table in `fixtures/README.md`. Check every ZWNJ by hand.

Name files `NN-source-topic.txt`; use UTF-8 and one paragraph or more per file.
Use LF line endings. A human must approve spelling and source provenance before
the file becomes a zero-issue baseline. Do not use this generator to author clean
text. The Persian instructions below are instructions, not a text sample.

## راهنمای افزودن متن

این پوشه فقط برای متن فارسی نوشتهٔ انسان و ویرایش~شده به دست ویراستار حرفه~ای
است. متن تولیدشده با هوش مصنوعی، حتی پس از بازنویسی، نباید در این پوشه قرار گیرد.
هر فایل متنی باید در لایهٔ محلی هیچ ایرادی ایجاد نکند.

از نوشته~های دقیق و ویرایش~شدهٔ نگهدارندهٔ پروژه یا مقاله~های برگزیدهٔ
ویکی~پدیای فارسی با مجوز CC BY-SA 4.0 استفاده کنید. مجوز و منشأ انسانی متن را
بررسی و نشانی مقاله، نسخه، نام پدیدآورندگان و اطلاعات انتساب را در جدول منابع
`fixtures/README.md` ثبت کنید. همهٔ نیم~فاصله~ها را دستی بررسی کنید.

نام فایل باید به صورت `NN-source-topic.txt` باشد و هر فایل دست~کم یک بند داشته
باشد. فایل را با رمزگذاری UTF-8 ذخیره کنید. این راهنما نمونهٔ متن پاک نیست.
""")


def fixture_readme(paths, rules):
    rows = "\n".join(
        "| `{}` | synthetic | CC0 | Original synthetic fixture material; no external text. |".format(path)
        for path in sorted(paths)
    )
    counts = "\n".join(
        "| {} | {} | {} |".format(rule, len(doc["cases"]), sum(c["kind"] == "negative" for c in doc["cases"]))
        for rule, doc in rules.items()
    )
    return """# Persian lint fixtures

These fixtures are the source of truth. Code generators must not modify curated
fixtures, and expected values must never be changed merely to make tests pass.
All generated material is an unreviewed proposal; it is not approved ground truth.

## Layout

- `normalizer/`: rule-level input/output pairs and paragraph-level integration cases.
- `ai-samples/`: six original synthetic examples of poor Persian style, each with
  exact-span LLM expectations; their orthography is intended to be clean.
- `clean/`: instructions only. Add exclusively human-written, professionally edited
  Persian prose for zero-local-issue baselines; never generate those samples.
- `schema/`: draft 2020-12 schemas for normalizer files and AI expectation files.

## Human review and test loading

1. A native Persian editor checks every input, expected result, configuration and
   note against modern Persian orthography, consulting the Academy's دستور خط فارسی
   for disputed spellings. Omit ambiguous transformations rather than guessing.
2. Review every AI sample and each issue's category, severity, verbatim quote and
   replacement. A replacement applies only to its quote. Recheck uniqueness after
   any edit. `must_detect` selects the three to five mandatory issues per sample.
3. The human reviewer sets a normalizer case's `reviewed` to `true` only after
   approving that case, and an AI expectation's `reviewed` to `true` only after
   approving its entire paired sample and all issues.
4. Tests must load only cases with `reviewed === true`; load an AI sample only when
   its expectation is reviewed. Report skipped unreviewed material explicitly:
   zero reviewed cases does not establish normalization correctness. These files
   provide data only; the existing test runner is not changed by the generator.
5. Preserve approved expectations when fixing implementation defects. Curated
   fixtures can change only through explicit human editorial review.

Run `python create_fixtures.py` from the repository root for initial seeding only.
The standard-library-only script validates the corpus before writing, overwrites
its 29 named output files deterministically, and never deletes other files.
Rerunning replaces its original proposals, including review flags: do not rerun
over human-reviewed or edited fixtures. Commit and maintain curated files directly;
do not edit the generator or regenerate expectations to satisfy implementation.

## Normalizer contract

Single-rule files isolate the named rule and span-protection behavior. `combined`
and `protected-spans` exercise all applicable rules together. Positive cases must
change; negative cases must remain exactly identical. At least 40% in every file
are negative. Preserve line breaks and paragraph breaks.

Options here are a fixture contract, not the application's current TypeScript
option names: `digits: "persian"` / `"keep"` and `hehYeStyle: "hamza"` / `"zwnj"`.
Omitted values mean Persian digits in Persian context and hamza-style ezafe.
A future loader should map `digits` to `persianDigits`, and `hehYeStyle` to
`ezafeStyle` (`"zwnj"` becomes `"ye"`); it must also isolate the requested rule.
Do not weaken these fixtures to match missing features of the current normalizer.
The alternate ZWNJ ezafe spelling is an explicit configurable style requirement.

URLs, emails, code, mentions, hashtags, complete Latin-script runs, structured
JSON-like spans and Markdown links are immutable, including Persian text or
punctuation inside them. Version ranges and English-context dates/phone numbers
are technical spans. Surrounding Persian still normalizes.

## Encoding and semantic validation

All files are UTF-8 with LF endings. JSON is indented, non-ASCII readable, and uses
the visible escape `\\u200c` for U+200C inside strings. Parsed JSON and `.txt` files
contain the real character. Source strings use a visible marker materialized from
the Python literal `"\\u200c"`; no invisible ZWNJs are pasted into the generator.
Word counts use whitespace splitting; a ZWNJ-joined form counts as one word.

The schemas validate required fields, enums, IDs, counts, negative coverage and
mandatory-issue counts. They allow human review flags to become true. The generator
additionally checks unique IDs, positive/negative equality semantics, unreviewed
flags, 120–250 words, and that each issue quote occurs verbatim exactly once.
These mechanical checks do not replace a human language review or an eventual
comparison with the local implementation. No model API is called.

## Coverage

| Rule | Cases | Negative cases |
| --- | ---: | ---: |
{counts}

Deliberately excluded: ambiguous blanket conversions of waw-hamza, ambiguous
compound-word segmentation, and quoted Arabic prose requiring language detection.
The accepted `مسئله` / `مسأله` variants remain unchanged as specified.

## Sources and licenses

All generated material is original synthetic material dedicated under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/); no external prose is
copied. The table lists every generated file, including schemas and instructions.
Replace/add rows with actual source, license and attribution when humans add clean
texts. Persian Wikipedia material must retain its own CC BY-SA 4.0 attribution and
license; it does not become CC0. No real people or companies occur in the samples;
`.invalid` domains and the reserved fictional phone number are placeholders.

| File (relative to fixtures/) | Source | License | Attribution |
| --- | --- | --- | --- |
{rows}
""".format(counts=counts, rows=rows)


def build_files():
    rules = normalizer_documents()
    samples = ai_documents()
    validate(rules, samples)
    normalizer_schema, ai_schema = schemas(rules)
    files = {
        "schema/normalizer-cases.schema.json": normalizer_schema,
        "schema/ai-sample-expected.schema.json": ai_schema,
        "clean/README.md": CLEAN_README,
    }
    for rule, document in rules.items():
        files["normalizer/{}.json".format(rule)] = document
    for name, (text, expected) in samples.items():
        files["ai-samples/{}.txt".format(name)] = text
        files["ai-samples/{}.expected.json".format(name)] = expected
    files["README.md"] = fixture_readme(list(files) + ["README.md"], rules)
    assert len(files) == 29, len(files)
    return files, rules, samples


def main():
    files, rules, samples = build_files()
    root = Path.cwd() / "fixtures"
    for name, value in sorted(files.items()):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name.endswith(".json"):
            content = json.dumps(value, ensure_ascii=False, indent=2).replace(ZWNJ, "\\u200c") + "\n"
        else:
            content = value
        assert "\r" not in content, name
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    print("Created/overwrote {} fixture files.".format(len(files)))
    for rule, document in rules.items():
        cases = document["cases"]
        negatives = sum(c["kind"] == "negative" for c in cases)
        print("  {}: {} cases ({} positive, {} negative)".format(rule, len(cases), len(cases) - negatives, negatives))
    print("Total normalizer cases: {}".format(sum(len(d["cases"]) for d in rules.values())))
    for name, (text, expected) in samples.items():
        print("  {}: {} words, {} issues ({} mandatory)".format(
            name, len(text.split()), len(expected["issues"]), sum(i["must_detect"] for i in expected["issues"]),
        ))


if __name__ == "__main__":
    main()

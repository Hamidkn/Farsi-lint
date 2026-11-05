# Farsi-lint Test Fixtures / داده‌های آزمون فارسی‌لینت

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
- **In `.json` files**: The Zero-Width Non-Joiner (U+200C) is stored explicitly as the 6-character sequence `\u200c`. This ensures the character is visually explicit in code reviews, pull requests, and terminal outputs.
- **In `.txt` files**: The real, standard UTF-8 binary character U+200C is used directly, matching realistic browser inputs.

## Sources and Licenses / منابع و مجوزها

| File / Folder | Source | License | Attribution |
| :--- | :--- | :--- | :--- |
| `schema/*.json` | synthetic | CC0-1.0 | Farsi-lint Core Team |
| `normalizer/*.json` | synthetic | CC0-1.0 | Farsi-lint Core Team |
| `ai-samples/*.txt` | synthetic | CC0-1.0 | Farsi-lint Core Team (simulating typical LLM translation pitfalls) |
| `ai-samples/*.expected.json` | synthetic | CC0-1.0 | Farsi-lint Core Team |
| `clean/` | human-authored | CC BY-SA 4.0 / CC0 | Documented per-file upon manual addition |

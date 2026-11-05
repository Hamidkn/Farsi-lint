# فارسی‌لینت | Farsi-lint
> A Manifest V3 Chrome extension (also compatible with Edge and Brave) for reviewing Persian (Farsi) text, specifically designed to detect AI-generated translationese, unnatural phrasing, and Persian orthography/typography issues.
> 
> افزونه مرورگر (Manifest V3) برای بازبینی و ویرایش متون فارسی، با تمرکز ویژه بر پالایش متون تولیدشده توسط هوش مصنوعی و اصلاح قواعد رسم‌الخط و نیم‌فاصله.

---

## 🌟 English Overview

Farsi-lint operates in two complementary layers:
1. **Local Rule-Based Layer (Offline & Instant)**:
   - Pure client-side functions running locally in the browser with zero network requests.
   - Converts Arabic characters (`ي`/`ك`/`ى`) to Persian (`ی`/`ک`).
   - Converts Arabic-Indic and English digits to Persian digits outside protected spans.
   - Inserts ZWNJ (نیم‌فاصله) for verbal prefixes (`می`/`نمی`), plural suffixes (`ها`/`های`), comparative suffixes (`تر`/`ترین`), and verbal/indefinite suffixes after silent heh (`رفته‌ام`, `دیده‌ای`, `خانه‌ای`).
   - Cleans redundant ZWNJ next to whitespace and collapses multiple spaces.
   - Normalizes Persian punctuation (`،`, `؛`, `؟`) with correct spacing rules.
   - English quotes `""` to Persian guillemets `«»`, and removes spaces inside brackets.
   - Converts `...` to `…` and removes decorative kashida (`ـ`).
   - Configurable ezafe style (`خانهٔ` vs `خانه‌ی`).
   - **Protected Spans Engine**: Never touches URLs, emails, code blocks, inline code, @mentions, #hashtags, version strings (e.g., `v2.1.0`), or Latin alphanumeric words (`MP3`, `UTF8`, `React19`).

2. **LLM Review Layer (On-Demand with User's Own API Key)**:
   - Evaluates Persian text against typical AI artifacts: translationese calques (`در پایان روز`, `این یک بازی‌تغییر است`), unnatural phrasing, preposition/ezafe errors, colloquial/formal register mixing, wrong collocations (`تصمیم ساختن` → `تصمیم گرفتن`), redundancy, and terminology inconsistency.
   - Works with **Anthropic Claude**, **OpenAI**, **OpenRouter**, **Google Gemini**, and local OpenAI-compatible endpoints (**Ollama**, **LM Studio**).
   - Strict Zod schema validation with automatic single retry on invalid JSON output.
   - Paragraph-based chunking (~1,500 words per chunk) with terminology memory passing across chunks.
   - Exact verbatim quote location and validation (hallucinated quotes not in the original text are safely discarded).

---

## 🚀 Installation & Setup

### How to load the unpacked extension in Chrome / Brave / Edge:
1. Download or clone this repository, or click the **"دانلود بسته افزونه (.zip)"** button in the web workbench.
2. In your browser, navigate to:
   - Chrome: `chrome://extensions`
   - Brave: `brave://extensions`
   - Edge: `edge://extensions`
3. Turn on the **Developer mode** toggle in the top-right corner.
4. Click **Load unpacked** and select the extension directory.
5. The Farsi-lint icon will appear in your browser toolbar!

### CLI Usage:
You can also run the local normalizer from the terminal:
```bash
# Check a Persian text file
npm run normalize -- sample.txt

# Automatically apply fixes to the file
npm run normalize -- sample.txt --fix

# Or pipe text through stdin
cat sample.txt | npm run normalize
```

---

## 📸 Features & UI/UX

1. **Side Panel (`chrome.sidePanel` API)**:
   - Opens via browser toolbar, context menu (*"بازبینی متن فارسی"*), or keyboard shortcut (`Ctrl+Shift+Y` / `Cmd+Shift+Y`).
   - Categorized issue filters with counts.
   - Per-issue Accept, Reject, and Edit suggestion.
   - *"Accept all orthography fixes"* button (bulk applies local layer only; never bulk accepts LLM suggestions).
   - Persian summary card and AI-likelihood stylistic note.
   - One-click *"Copy corrected text"* button.

2. **Inline Underlines & Floating Button**:
   - Automatically appears when any editable field (`textarea`, `input[type=text]`, `contenteditable`, Gmail compose, LinkedIn/X post box) contains >30% Persian characters.
   - Wavy underline overlays: **Red** (errors), **Orange** (warnings), **Blue** (suggestions).
   - Hovering displays explanation and 1-click replacement via `document.execCommand('insertText')` to preserve browser undo history and React state.

3. **Privacy First**:
   - Zero telemetry, zero analytics.
   - API keys are stored exclusively in `chrome.storage.local` (never synced).
   - Automatically disabled on password fields (`input[type=password]`), credit card inputs (`autocomplete="cc-*"`), and configurable site blacklist.

---

## ⚠️ Known Limitations

- **Google Docs**: Renders text using an HTML5 Canvas element instead of standard DOM text nodes. Direct DOM overlays cannot measure character bounding boxes in Google Docs; a friendly prompt directs users to copy text into the Farsi-lint Side Panel.
- **Complex Bidi with Mixed Code**: Highly nested bidirectional sentences with bidirectional punctuation (e.g. Persian parentheses inside regex inside code blocks) rely on the protected spans detector to avoid altering code tokens.

---

## 🇮🇷 راهنمای فارسی

### لایه‌های عملکردی:
1. **لایه محلی رسم‌الخط (آفلاین و آنی)**:
   - تبدیل حروف عربی (ي/ك/ى) به ی و ک فارسی
   - تبدیل اعداد به ارقام فارسی به جز در لینک‌ها، کدها، ایمیل‌ها و شناسه‌های نسخه (مانند v2.1.0)
   - تنظیم دقیق نیم‌فاصله برای پیشوندها (می/نمی) و پسوندها (ها/های/تر/ترین/پسوندهای بعد از ه)
   - عدم دستکاری کلمات مستقل مانند «میز»، «میوه»، «میهن»، «هایل» یا «ترس»
   - اصلاح نشانه‌گذاری (، ؛ ؟) و گیومه‌ها (« »)

2. **لایه بازبینی هوش مصنوعی (درخواستی)**:
   - تشخیص گرته‌برداری و ترجمه‌های لفظی انگلیسی (مانند «در پایان روز»)
   - اصلاح همایندی‌های نادرست (مانند «تصمیم ساختن»)
   - بررسی یکدستی اصطلاحات و تفکیک لحن رسمی و محاوره‌ای
   - پشتیبانی از تمام ارائه‌دهندگان معتبر (OpenAI، Anthropic Claude، OpenRouter، Google Gemini و Ollama)

### دستورات ترمینال:
```bash
# بررسی متن از طریق خط فرمان
npm run normalize -- file.txt

# اعمال خودکار اصلاحات
npm run normalize -- file.txt --fix

# اجرای آزمون‌های واحد (Unit Tests)
npm test
```

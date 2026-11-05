# Clean Persian Text Corpus / پیکره متون پاکیزه فارسی

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

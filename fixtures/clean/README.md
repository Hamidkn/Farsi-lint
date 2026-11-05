# Human-written clean corpus

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

این پوشه فقط برای متن فارسی نوشتهٔ انسان و ویرایش‌شده به دست ویراستار حرفه‌ای
است. متن تولیدشده با هوش مصنوعی، حتی پس از بازنویسی، نباید در این پوشه قرار گیرد.
هر فایل متنی باید در لایهٔ محلی هیچ ایرادی ایجاد نکند.

از نوشته‌های دقیق و ویرایش‌شدهٔ نگهدارندهٔ پروژه یا مقاله‌های برگزیدهٔ
ویکی‌پدیای فارسی با مجوز CC BY-SA 4.0 استفاده کنید. مجوز و منشأ انسانی متن را
بررسی و نشانی مقاله، نسخه، نام پدیدآورندگان و اطلاعات انتساب را در جدول منابع
`fixtures/README.md` ثبت کنید. همهٔ نیم‌فاصله‌ها را دستی بررسی کنید.

نام فایل باید به صورت `NN-source-topic.txt` باشد و هر فایل دست‌کم یک بند داشته
باشد. فایل را با رمزگذاری UTF-8 ذخیره کنید. این راهنما نمونهٔ متن پاک نیست.

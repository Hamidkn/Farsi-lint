/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, it, expect } from 'vitest';
import { normalizePersianText, getPersianCharacterRatio } from '../src/core/normalizer/index.ts';
import { applyIssues } from '../src/core/diff/index.ts';

describe('Persian Normalizer (core/normalizer)', () => {
  describe('Rule 1: Arabic Characters (ي/ك/ى → ی/ک)', () => {
    it('converts Arabic Yeh to Persian Yeh', () => {
      const text = 'علي و مهدي در خيابان هستند.';
      const issues = normalizePersianText(text, { persianDigits: false });
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('علی و مهدی در خیابان هستند.');
      expect(issues.some((i) => i.ruleId === 'arabic-chars')).toBe(true);
    });

    it('converts Arabic Kaf to Persian Kaf', () => {
      const text = 'كتاب كودك در كلاس است.';
      const issues = normalizePersianText(text, { persianDigits: false });
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('کتاب کودک در کلاس است.');
    });

    it('converts Arabic Alef Maksura to Persian Yeh', () => {
      const text = 'موسي و عيسي';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('موسی و عیسی');
    });

    it('does not touch characters inside code blocks or URLs', () => {
      const text = 'متن فارسی https://site.com/كتاب `كودك_code` ادامه';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toContain('https://site.com/كتاب');
      expect(fixed).toContain('`كودك_code`');
    });
  });

  describe('Rule 2: Digits Conversion & Protected Spans', () => {
    it('converts English digits to Persian digits in Persian context', () => {
      const text = 'در سال 1403 تعداد 25 نفر شرکت کردند.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('در سال ۱۴۰۳ تعداد ۲۵ نفر شرکت کردند.');
    });

    it('converts Arabic-Indic digits to Persian digits', () => {
      const text = 'قیمت ٥٠٠٠ تومان است.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('قیمت ۵۰۰۰ تومان است.');
    });

    it('never converts digits inside English words (e.g. MP3, UTF8, React19)', () => {
      const text = 'فایل MP3 با فرمت UTF8 در React19 ذخیره شد.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toContain('MP3');
      expect(fixed).toContain('UTF8');
      expect(fixed).toContain('React19');
    });

    it('never converts digits inside version numbers (e.g. v2.1.0, 1.0.4)', () => {
      const text = 'نسخه جدید v2.1.0 و نسخه 1.0.4 منتشر شد.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toContain('v2.1.0');
      expect(fixed).toContain('1.0.4');
    });

    it('never converts digits inside URLs or emails', () => {
      const text = 'ایمیل user123@domain456.com و آدرس https://api.site.com/v1/page?id=99';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toContain('user123@domain456.com');
      expect(fixed).toContain('https://api.site.com/v1/page?id=99');
    });

    it('never converts digits inside @mentions or #hashtags', () => {
      const text = 'ارسال به @user2024 با هشتگ #iran1403';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toContain('@user2024');
      expect(fixed).toContain('#iran1403');
    });
  });

  describe('Rule 3: ZWNJ for Prefixes & Suffixes & Tricky Words', () => {
    it('adds ZWNJ after prefix می', () => {
      const text = 'او به خانه می رود.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('او به خانه می‌رود.');
    });

    it('adds ZWNJ after prefix نمی', () => {
      const text = 'من حقیقت را نمی دانم.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('من حقیقت را نمی‌دانم.');
    });

    it('CRITICAL: never splits words like میز (table)', () => {
      const text = 'میز کار تمیز است.';
      const issues = normalizePersianText(text);
      expect(issues.some((i) => i.original.includes('میز'))).toBe(false);
      expect(applyIssues(text, issues)).toBe('میز کار تمیز است.');
    });

    it('CRITICAL: never splits words like میوه، میهن، میعاد، میراث، میلاد', () => {
      const text = 'میوه تازه در میهن ما و در روز میلاد خجسته است.';
      const issues = normalizePersianText(text);
      expect(issues.length).toBe(0);
      expect(applyIssues(text, issues)).toBe(text);
    });

    it('adds ZWNJ for plural suffix ها', () => {
      const text = 'کتاب ها روی میز هستند.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('کتاب‌ها روی میز هستند.');
    });

    it('adds ZWNJ for suffix های', () => {
      const text = 'پنجره های بزرگ باز شدند.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('پنجره‌های بزرگ باز شدند.');
    });

    it('CRITICAL: never splits words like هایل (hail) or هایکو', () => {
      const text = 'شاعر یک هایکو زیبا خواند و هایل بارید.';
      const issues = normalizePersianText(text);
      expect(issues.some((i) => i.original.includes('هایکو') || i.original.includes('هایل'))).toBe(false);
    });

    it('adds ZWNJ for comparative suffix تر and ترین', () => {
      const text = 'این درخت بزرگ تر و آن گل زیبا ترین است.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('این درخت بزرگ‌تر و آن گل زیباترین است.');
    });

    it('CRITICAL: never splits words like ترس، تربت، ترنج، ترک', () => {
      const text = 'او از تاریکی هیچ ترس و واهمه‌ای ندارد.';
      const issues = normalizePersianText(text);
      expect(issues.some((i) => i.original.includes('ترس'))).toBe(false);
    });

    it('adds ZWNJ for suffixes after silent heh: ام/ای/ایم/اید/اند', () => {
      const text = 'من رفته ام و او را دیده ای و ما آمده ایم و شما شنیده اید و آنها رسیده اند.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('من رفته‌ام و او را دیده‌ای و ما آمده‌ایم و شما شنیده‌اید و آن‌ها رسیده‌اند.');
    });

    it('adds ZWNJ for indefinite suffix ای after heh: خانه ای', () => {
      const text = 'در گوشه‌ای از شهر خانه ای قدیمی دیدم.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('در گوشه‌ای از شهر خانه‌ای قدیمی دیدم.');
    });
  });

  describe('Rule 4: Redundant ZWNJ & Whitespace Cleanup', () => {
    it('removes ZWNJ adjacent to spaces', () => {
      const text = 'کلمه \u200c دیگر و کلمه\u200c دیگر';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('کلمه دیگر و کلمه دیگر');
    });

    it('collapses multiple consecutive ZWNJs into one', () => {
      const text = 'می\u200c\u200cروم';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('می‌روم');
    });

    it('collapses multiple spaces into a single space', () => {
      const text = 'فاصله    بسیار    زیاد    است.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('فاصله بسیار زیاد است.');
    });
  });

  describe('Rule 5: Punctuation Marks (، ؛ ؟) and Spacing', () => {
    it('converts English comma, semicolon, and question mark to Persian', () => {
      const text = 'سلام, چطوری? حالت خوبه; بله.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('سلام، چطوری؟ حالت خوبه؛ بله.');
    });

    it('removes space before punctuation marks', () => {
      const text = 'کتاب ، دفتر ؛ و قلم ؟';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('کتاب، دفتر؛ و قلم؟');
    });

    it('adds missing space after punctuation when followed by words', () => {
      const text = 'سلام،من امروز آمدم؛اما تو نبودی.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('سلام، من امروز آمدم؛ اما تو نبودی.');
    });

    it('does not tamper with colon in time format like 14:30', () => {
      const text = 'جلسه در ساعت 14:30 آغاز می‌شود.';
      const issues = normalizePersianText(text, { persianDigits: false });
      const fixed = applyIssues(text, issues);
      expect(fixed).toContain('14:30');
    });
  });

  describe('Rule 6: Quotes and Brackets', () => {
    it('converts English double quotes to Persian guillemets «»', () => {
      const text = 'او گفت "دانش توانایی است" و رفت.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('او گفت «دانش توانایی است» و رفت.');
    });

    it('removes space inside brackets ( text ) -> (text)', () => {
      const text = 'برنامه ( فاز اول ) آغاز شد [ گروه دوم ].';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('برنامه (فاز اول) آغاز شد [گروه دوم].');
    });
  });

  describe('Rule 7: Ellipsis and Kashida Removal', () => {
    it('converts three dots ... to ellipsis …', () => {
      const text = 'ادامه دارد... و پایان یافت.';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('ادامه دارد… و پایان یافت.');
    });

    it('removes kashida (ـ) stretching', () => {
      const text = 'ســـلام و احـــترام';
      const issues = normalizePersianText(text);
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('سلام و احترام');
    });
  });

  describe('Rule 8: Ezafe Style ("ه ی" → "هٔ" or "هی")', () => {
    it('converts "خانه ی" to "خانهٔ" in hamza mode', () => {
      const text = 'خانه ی پدری بسیار باصفا بود.';
      const issues = normalizePersianText(text, { ezafeStyle: 'hamza' });
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('خانهٔ پدری بسیار باصفا بود.');
    });

    it('converts "خانه ی" to "خانه‌ی" in ye mode', () => {
      const text = 'خانه ی پدری بسیار باصفا بود.';
      const issues = normalizePersianText(text, { ezafeStyle: 'ye' });
      const fixed = applyIssues(text, issues);
      expect(fixed).toBe('خانه‌ی پدری بسیار باصفا بود.');
    });
  });

  describe('Persian Character Ratio Helper', () => {
    it('calculates > 30% for Persian text', () => {
      const text = 'این یک متن کاملاً فارسی است.';
      expect(getPersianCharacterRatio(text)).toBeGreaterThan(0.9);
    });

    it('calculates < 30% for predominantly English text', () => {
      const text = 'This is an English paragraph with single word سلام.';
      expect(getPersianCharacterRatio(text)).toBeLessThan(0.3);
    });
  });

  describe('Zero False Positives on Clean, Professionally Edited Persian (15+ Paragraphs)', () => {
    const cleanFixtures = [
      // 1. Saadi Shirazi - Golestan (Preface)
      'منت خدای را عز و جل که طاعتش موجب قربت است و به شکر اندرش مزید نعمت. هر نفسی که فرو می‌رود ممد حیات است و چون برمی‌آید مفرح ذات.',
      // 2. Ferdowsi - Shahnameh (Prologue)
      'به نام خداوند جان و خرد، کزین برتر اندیشه برنگذرد. خداوند نام و خداوند جای، خداوند روزی‌ده و رهنمای.',
      // 3. Hafez Shirazi - Ghazal
      'اگر آن ترک شیرازی به دست آرد دل ما را، به خال هندویش بخشم سمرقند و بخارا را. بده ساقی می باقی که در جنت نخواهی یافت، کنار آب رکناباد و گلگشت مصلا را.',
      // 4. Modern Literary Prose (Zarrinkoub)
      'با کاروان حله، تصویری از سیر اندیشه در قلمرو ادبیات فارسی است. نویسنده با زبانی شیوا و نثری استوار، مخاطب را به تماشای شاهکارهای جاودان ادب فارسی فرامی‌خواند.',
      // 5. Contemporary History & Philosophy
      'تاریخ بیهقی آیینه تمام‌نمای روزگار غزنویان است که در آن، صداقت مورخ با هنر نویسندگی در هم آمیخته و اثری ماندگار پدید آورده است.',
      // 6. Scientific Prose (Astronomy)
      'کهکشان راه شیری شامل میلیاردها ستاره است که حول یک مرکز جرم مشترک با سرعتی سرسام‌آور گردش می‌کنند و سامانه‌های سیاره‌ای متعددی را در بر دارند.',
      // 7. Technology & Software
      'توسعه نرم‌افزارهای مدرن نیازمند درک عمیق از ساختار داده‌ها، الگوریتم‌های بهینه و معماری مقیاس‌پذیر در بستر وب است.',
      // 8. Literary Criticism
      'شعر نو فارسی با نیما یوشیج آغاز شد و با تلاش شاعرانی چون اخوان ثالث، سهراب سپهری و فروغ فرخزاد به اوج پختگی و کمال بیانی رسید.',
      // 9. Environmental Science
      'حفاظت از تنوع زیستی تالاب‌ها و مراتع کوهستانی نقش بنیادینی در پایداری چرخه‌های آب شیرین و مهار بحران‌های فرسایش خاک ایفا می‌کند.',
      // 10. Encyclopedia Entry (Tehran)
      'تهران پرجمعیت‌ترین شهر و پایتخت ایران است که در دامنه‌های جنوبی رشته‌کوه البرز واقع شده و کانون فعالیت‌های اقتصادی، دانشگاهی و فرهنگی کشور به شمار می‌آید.',
      // 11. Architecture & Arts
      'معماری سنتی ایران در شهرهایی چون اصفهان، یزد و کاشان نمونه‌ای بی‌همتا از تلفیق اقلیم، هنر کاشی‌کاری، بادگیرها و حیاط‌های مرکزی سرسبز است.',
      // 12. Philosophy of Mind
      'بررسی نسبت میان آگاهی، مغز و شناخت از پیچیده‌ترین پرسش‌های دانش امروز است که مرزهای میان فلسفه، هوش مصنوعی و علوم اعصاب را در هم می‌نوردد.',
      // 13. Linguistics & Persian Lexicography
      'فرهنگ لغت دهخدا بزرگ‌ترین و جامع‌ترین فرهنگ واژگان زبان فارسی است که با تلاشی خستگی‌ناپذیر و پژوهشی ژرف در متون کهن تدوین یافته است.',
      // 14. Cultural Heritage
      'موسیقی سنتی و دستگاهی ایران ریشه در سنت‌های کهن خنیاگری دارد و گوشه‌های آن راویان اندوه، شور و ژرفای جان انسانی در بستر قرن‌ها هستند.',
      // 15. Modern Journalism / Economy
      'سیاست‌های پولی و مالی هوشمندانه می‌توانند نوسانات تورمی را مهار کنند و زمینه را برای سرمایه‌گذاری مولد در صنایع دانش‌بنیان فراهم آورند.',
      // 16. Professional Essay
      'خواندن کتاب‌های ارزشمند افق دید آدمی را گسترش می‌دهد و توانایی اندیشیدن نقادانه را در مواجهه با انبوه داده‌های عصر دیجیتال تقویت می‌بخشد.',
    ];

    cleanFixtures.forEach((paragraph, idx) => {
      it(`produces zero issues on clean paragraph #${idx + 1}`, () => {
        const issues = normalizePersianText(paragraph);
        if (issues.length > 0) {
          console.error(`Unexpected issues in clean fixture #${idx + 1}:`, issues);
        }
        expect(issues.length).toBe(0);
      });
    });
  });
});

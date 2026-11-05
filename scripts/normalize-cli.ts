/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import fs from 'node:fs';
import { normalizePersianText } from '../src/core/normalizer/index.ts';
import { applyIssues } from '../src/core/diff/index.ts';

function main() {
  const args = process.argv.slice(2);

  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log(`
فارسی‌لینت (Farsi-lint CLI)
استفاده:
  npm run normalize -- <file.txt> [--fix]
  cat file.txt | npm run normalize
`);
    process.exit(0);
  }

  let filePath = '';
  let autoFix = false;

  for (const arg of args) {
    if (arg === '--fix') {
      autoFix = true;
    } else if (!filePath) {
      filePath = arg;
    }
  }

  let text = '';
  if (filePath) {
    if (!fs.existsSync(filePath)) {
      console.error(`خطا: فایل یافت نشد: ${filePath}`);
      process.exit(1);
    }
    text = fs.readFileSync(filePath, 'utf-8');
  } else {
    text = fs.readFileSync(0, 'utf-8'); // stdin
  }

  console.log(`\nدر حال بررسی متن (${text.length} نویسه)...\n`);
  const issues = normalizePersianText(text);

  if (issues.length === 0) {
    console.log('✓ هیچ ایرادی در رسم‌الخط، فاصله‌گذاری و نشانه‌گذاری متن یافت نشد (متن پاکیزه است).');
    process.exit(0);
  }

  console.log(`تعداد ${issues.length} ایراد ویرایشی یافت شد:\n`);

  for (let i = 0; i < issues.length; i++) {
    const issue = issues[i];
    console.log(
      `[${i + 1}] موقعیت ${issue.start}..${issue.end} | ${issue.category} (${issue.ruleId}):`
    );
    console.log(`     اصل:       «${issue.original}»`);
    console.log(`     پیشنهاد:    «${issue.suggestion}»`);
    console.log(`     توضیح:     ${issue.explanation}\n`);
  }

  const fixed = applyIssues(text, issues);

  if (autoFix) {
    console.log('--- متن اصلاح‌شده ---');
    console.log(fixed);
  } else {
    console.log('برای اعمال خودکار اصلاحات، از پرچم --fix استفاده کنید:');
    console.log(`npm run normalize -- ${filePath || 'file.txt'} --fix`);
  }
}

main();

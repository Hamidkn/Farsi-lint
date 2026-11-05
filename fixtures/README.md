# Persian lint fixtures

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
the visible escape `\u200c` for U+200C inside strings. Parsed JSON and `.txt` files
contain the real character. Source strings use a visible marker materialized from
the Python literal `"\u200c"`; no invisible ZWNJs are pasted into the generator.
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
| arabic-letters | 20 | 8 |
| digits | 20 | 11 |
| zwnj | 25 | 10 |
| zwnj-cleanup | 20 | 8 |
| spaces | 15 | 6 |
| punctuation | 15 | 6 |
| quotes | 15 | 6 |
| brackets-spacing | 15 | 6 |
| ellipsis | 15 | 6 |
| kashida | 15 | 6 |
| heh-ye | 20 | 10 |
| protected-spans | 20 | 10 |
| combined | 10 | 4 |

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
| `README.md` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/01-formal-email.expected.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/01-formal-email.txt` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/02-linkedin-post.expected.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/02-linkedin-post.txt` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/03-translated-tech-article.expected.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/03-translated-tech-article.txt` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/04-customer-support.expected.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/04-customer-support.txt` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/05-product-description.expected.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/05-product-description.txt` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/06-mixed-register.expected.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `ai-samples/06-mixed-register.txt` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `clean/README.md` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/arabic-letters.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/brackets-spacing.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/combined.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/digits.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/ellipsis.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/heh-ye.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/kashida.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/protected-spans.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/punctuation.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/quotes.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/spaces.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/zwnj-cleanup.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `normalizer/zwnj.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `schema/ai-sample-expected.schema.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |
| `schema/normalizer-cases.schema.json` | synthetic | CC0 | Original synthetic fixture material; no external text. |

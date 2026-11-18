# Group-coding audit for AF, QA, NR (ML1 cleaned dataset, labels file)

Source: `data/raw/ml1/extracted/data/Data/Tab.delimited.Cleaned.dataset.WITH.variable.labels.dat`, 6344 rows; numeric-code twin `data/raw/ml1/extracted/data/Data/Tab.delimited.Cleaned.dataset.WITH.variable.values.dat`. Written by `analysis/human_ml1/acme_items.py build`. The condition x used for every value is the question the respondent answered (which of the two item variables is non-missing); the released group variable is only audited against it.

## AF allowed/forbidden
Codebook: `allowedforbiddena` = forbid question, `allowedforbiddenb` = allow question; 1 = Yes, 2 = No.

Group variable `allowedforbiddenGroup` against the question answered (counts of respondents):

| group_var | forbid Q answered; allow Q blank | forbid Q blank; allow Q answered | forbid Q blank; allow Q blank |
|---|---|---|---|
| allowed | 0 | 3122 | 52 |
| forbidden | 3170 | 0 | 0 |


Respondents who answered both questions: 0. Respondents who answered neither: 52 (missing, dropped; the file notes 52 invalid responses). Respondents whose answered question contradicts the group variable (answered the allow question while grouped 'forbidden', or the reverse): **0**.

Released composite `allowedforbidden` (YES/NO) against the raw Yes of the answered question: 0 mismatches (composite non-missing 6292, raw non-missing 6292).

Result: x1 (forbid) n = 3170, share anti-speech (Yes to forbid) = 0.0722; x0 (allow) n = 3122, share anti-speech (No to allow) = 0.2373. The coding is the one in the ML1 supplement (7.2 percent Yes to forbid, 23.7 percent No to allow).

**Note on the published ML1 effect for this item.** The supplement's chi-square (3088.69, d = 1.96) compares the raw Yes answer across the two questions, so it measures opposite positions against each other (Yes to forbid is anti-speech, Yes to allow is pro-speech). The anti-speech coding used here (and by Rugg 1941) gives a much smaller effect; the raw-Yes coding is kept as the metric `check_ml1_published_yes_coding` in `site_effects.csv` and reproduces the published number. See REPORT.md.


## QA quote attribution
Codebook: `quotea` = Washington, `quoteb` = Bin Laden; 1 = strongly agree, 9 = strongly disagree. Analysed y = 10 - raw (higher = more agreement), which equals the released `quote` variable.

Group variable `quoteGroup` against the quote answered:

| group_var | Washington answered; bin Laden blank | Washington blank; bin Laden answered | Washington blank; bin Laden blank |
|---|---|---|---|
| disliked source | 0 | 3083 | 19 |
| liked source | 3242 | 0 | 0 |


Answered both: 0. Answered neither: 19 (the supplement notes 19 invalid responses). Contradicting the group variable: **0**.

Recoded y against released `quote`: 0 mismatches; values outside 1..9: 0.

Result: Washington (x1) n = 3242, mean = 5.928, SD = 2.207; bin Laden (x0) n = 3083, mean = 5.232, SD = 2.113 (supplement: 5.93 / 2.2 and 5.23 / 2.11).


## NR norm of reciprocity
Codebook: `reciprocityusa` = US question asked first, `reciprocityusb` = US question asked second (other-country question first); `reciprocityothera` = other-country question asked second, `reciprocityotherb` = asked first; 1 = Yes, 2 = No. x1 = other first (US second), x0 = US first; y = 1 if Yes to the US question.

Group variable `reciprocitygroup` ('Asked first' / 'Asked second' refers to the US question) against the US question answered:

| group_var | US Q first-version (usa) answered; US Q second-version (usb) blank | US Q first-version (usa) blank; US Q second-version (usb) answered | US Q first-version (usa) blank; US Q second-version (usb) blank |
|---|---|---|---|
| Asked first | 3202 | 0 | 0 |
| Asked second | 0 | 3074 | 68 |


Same group variable against the other-country question answered:

| group_var | other Q second-version (othera) answered; other Q first-version (otherb) blank | other Q second-version (othera) blank; other Q first-version (otherb) answered | other Q second-version (othera) blank; other Q first-version (otherb) blank |
|---|---|---|---|
| Asked first | 3181 | 0 | 21 |
| Asked second | 15 | 3074 | 53 |


Answered both US versions: 0. Answered neither: 68 (the supplement notes 68 invalid responses). Contradicting the group variable: **0**. Respondents whose US-question version and other-country-question version imply different orders: **0**.

Recoded y against released `reciprocityus`: 0 mismatches.

Result: US question second (x1) n = 3074, share Yes = 0.7733; US question first (x0) n = 3202, share Yes = 0.6393 (supplement: 77.3 and 63.9 percent).


## Cross-check against the numeric-code file

- AF: label -> numeric code in the values file: allowed -> ['0']; forbidden -> ['1']
- QA: label -> numeric code in the values file: disliked source -> ['0']; liked source -> ['1']
- NR: label -> numeric code in the values file: Asked first -> ['1']; Asked second -> ['0']


## Sites
- AF: 6292 usable respondents, 36 sites, smallest arm within a site 33, x counts {1: 3170, 0: 3122}
- QA: 6325 usable respondents, 36 sites, smallest arm within a site 34, x counts {1: 3242, 0: 3083}
- NR: 6276 usable respondents, 36 sites, smallest arm within a site 34, x counts {0: 3202, 1: 3074}
- Site keys (`referrer`, as in build_tidy.py) identical to P1.csv: True (36 sites).

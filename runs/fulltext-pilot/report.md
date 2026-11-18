# Full-text reference pilot (amendment v0.8 C): PILOT, not a validation

Used 53 of 70 (no open full text 17, unclear 0); reference YES 32; decisions confirmed by Shlok: 40.

| rule | false exclusions / reference YES | rate [Wilson 95%] | false inclusions / reference NO | rate [Wilson 95%] |
|---|---|---|---|---|
| strict | 9/32 | 0.281 (0.156, 0.454) | 15/21 | 0.714 (0.5, 0.862) |
| liberal | 5/32 | 0.156 (0.069, 0.318) | 18/21 | 0.857 (0.654, 0.95) |
| claude | 4/32 | 0.125 (0.05, 0.281) | 9/21 | 0.429 (0.245, 0.635) |
| olmo | 11/32 | 0.344 (0.204, 0.517) | 18/21 | 0.857 (0.654, 0.95) |
| qwen | 9/32 | 0.281 (0.156, 0.454) | 16/21 | 0.762 (0.549, 0.894) |

By cell (Claude/OLMo): EXCLUDE/INCLUDE: n 9, YES 2, FE strict 0, FE liberal 0; EXCLUDE/MAYBE: n 7, YES 2, FE strict 0, FE liberal 0; INCLUDE/EXCLUDE: n 7, YES 6, FE strict 2, FE liberal 2; INCLUDE/MAYBE: n 9, YES 9, FE strict 0, FE liberal 0; MAYBE/EXCLUDE: n 7, YES 5, FE strict 4, FE liberal 3; MAYBE/INCLUDE: n 8, YES 4, FE strict 0, FE liberal 0; MAYBE/MAYBE: n 6, YES 4, FE strict 3, FE liberal 0

Strict vs liberal discordant records: [{'pilot_id': 'F13', 'ref': 'NO', 'cell': 'EXCLUDE/MAYBE'}, {'pilot_id': 'F19', 'ref': 'NO', 'cell': 'EXCLUDE/MAYBE'}, {'pilot_id': 'F45', 'ref': 'YES', 'cell': 'MAYBE/EXCLUDE'}, {'pilot_id': 'F61', 'ref': 'YES', 'cell': 'MAYBE/MAYBE'}, {'pilot_id': 'F66', 'ref': 'NO', 'cell': 'MAYBE/MAYBE'}, {'pilot_id': 'F68', 'ref': 'YES', 'cell': 'MAYBE/MAYBE'}, {'pilot_id': 'F70', 'ref': 'YES', 'cell': 'MAYBE/MAYBE'}]
Records with no INCLUDE vote: {'n': 12, 'ref_yes': 7, 'rq1_codable': 4}
Switch rule (pre-set): {'diff_false_excl_pp': 12.5, 'records_driving_difference': 4, 'outcome': 'liberal becomes primary'}

# W0 source note

W0 is the Many Labs 1 US wording, copied from `data/raw/ml1/materials/Measures_US_Version.docx`
(OSF project xvpu3, file "Measures_US_Version.docx", SHA-256 in `data/manifest.jsonl`).
The .docx has no fixed pagination; locations are the section headings in document order
(plain text extracted to `data/raw/ml1/md/Measures_US_Version.txt`, line numbers in brackets).

| Paradigm | Section heading in the .docx | Lines | Note |
|---|---|---|---|
| P1 gain/loss framing | "Disease Framing", conditions "Saved" (Programs A/B) and "Will die" (Programs C/D) | 130-143 | Wording verbatim; the gain-frame sure line has no final period in the source and none here. Labels A/B (gain) and C/D (loss) are as in ML1. |
| P2a to P2d anchoring | "Anchoring", items (SF to NY), (Chicago), (Everest), (babies), high and low conditions | 237-263 | Items verbatim. The page introduction ("For each of the following 4 questions ...") is adapted to one question per prompt: "For the following question we would like you to give your best estimate." |
| P3 sunk costs | "Sunk costs:", Paid and Free conditions, 9-point scale | 144-151 | Scenario verbatim. The scale ("1 - Definitely stay at home, 9 - Definitely go to the game") is rewritten as one sentence. |
| P4 retrospective gambler's fallacy | "Retrospective Gambler's Fallacy", "Common outcome" (one 3, two 6's) and "Rare outcome" (three 6's) | 67-72 | Wording verbatim. |

Coding of x (condition) used everywhere: x1 = the condition with the canonical higher outcome
(gain frame / high anchor / paid ticket / three 6s), x0 = the other.

ML1 item order note (E4, from the released data): data variable `anchoring1` has values between the
anchors 1,500 and 6,000 (distance), `anchoring2` 200,000 to 5,000,000 (Chicago), `anchoring3` 2,000 to
45,500 (Everest), `anchoring4` 100 to 50,000 (babies). P2a to P2d follow that order.

Units: US version (miles, feet) is canonical, as in the design.

# Pending reference checks, CRP-S09 (2026-11-07)

## (a) Cummins, "The Threat of Analytic Flexibility in Using Large Language Models to Simulate Human Data" (AMPPS 9(3), 2026)

Record. Crossref `10.1177/25152459261461505` (read 2026-11-07): Advances in Methods and Practices in Psychological Science 9(3), article 25152459261461505,
published online 2026-07-30, print July 2026, one author, CC BY 4.0, no `update-to`, no retraction or correction notice. Crossref lists the peer-review
trail (`v1` to `v3` reviews, decisions and author responses; the v3 author response is dated 2026-05-10). arXiv 2509.13397 has v1 2025-09-16, v2 2025-09-18,
v3 2026-04-17 and v4 2026-05-18 (v4 was posted eight days after the v3 author response; that the published text equals v4 is an inference, not a verified fact).

Published full text: **not read**. The publisher page returned HTTP 403 to the fetch tool, the article is not in Europe PMC, and OpenAlex lists no
repository copy other than arXiv. I did not try to get around the 403. Statements below about the published version rest on the Crossref abstract.

arXiv v4 (read from the PDF, converted with markitdown): the split-half benchmark is there.
- Method: the human data are split at random into two halves, the Wasserstein distance between the halves is computed, and this is repeated 2000 times, which gives
  the split-half reference interval for each scale (v4 Study 1 method; BJW scale interval [0.02, 0.09]).
- Results: the independent-human benchmark error has a median of |delta r| = .24 (95% interval .01 to .70) and the silicon error a median of .26 (.01 to .73);
  at least one silicon configuration beat the independent-human benchmark in 99.7% of splits, while the mean share of configurations doing so within a split was 45.4%.

Where the paper cites Cummins (grep `cummins2026flexibility` in `paper/acme/*.tex`):
1. `01-introduction.tex:107-108`: "Cummins compares the spread of Wasserstein distances over 252 configurations with the distance between random halves of one human sample, repeated 2,000 times".
   Supported by arXiv v4 (252 configurations; 2000 random splits; Wasserstein distance). Published version: **252 configurations is supported** by the Crossref abstract;
   **the split-half comparison and the 2,000 repetitions are not verifiable** without the published full text (the abstract does not mention them). The sentence carries no 0.24, 0.26 or 99.7 figure.
2. `05-state-of-art-validation.tex:128-130`: "Across 252 silicon-sample configurations, correspondence with human data varied on rankings, response distributions and scale correlations, and a configuration that did well on one criterion often did poorly on another."
   **Supported by the published abstract** (252 configurations on two scales; performance varied across participant rankings, response distributions and between-scale correlations; configurations strong on one criterion often failed on another).

Verdict. Sentence 2: supported by the published version. Sentence 1: supported by preprint v4, partly supported by the published abstract (252); the split-half part is pending.
The numbers 0.24 vs 0.26 and 99.7% are not used anywhere in the manuscript, so nothing needs to change unless they are added; if they are added, cite them as arXiv v4 or check the AMPPS text first.
Bib entry `cummins2026flexibility` already cites the AMPPS version with the DOI; its `pages = {25152459261461505}` is the article number (Crossref gives no page range).
Action for the authors: open the CC BY article at https://doi.org/10.1177/25152459261461505 in a browser and search for "split" and "2000".

## (b) ASME V&V 40-2018

Sources read 2026-11-07: ASME product page
(https://www.asme.org/codes-standards/find-codes-standards/assessing-credibility-of-computational-modeling-through-verification-and-validation-application-to-medical-devices)
and the FDA recognised-consensus-standards entry (https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfstandards/detail.cfm?standard__identification_no=38534).
- Title: "Assessing Credibility of Computational Modeling through Verification and Validation: Application to Medical Devices" (the FDA entry capitalises "Through").
- Designation: ASME V&V 40-2018 (the ASME page shows "V V 40 - 2018"). Year 2018. Publisher and developer: The American Society of Mechanical Engineers (ASME).
- FDA recognition number 5-122, entered 2019-01-14. ASME status: stabilized maintenance, "remains in effect".
- DOI: none listed on either page. ISBN is not listed on the ASME page (a reseller snippet gives 9780791872048; not used).
- The ASME page says the subcommittee considers the standard general enough to apply to other disciplines, which supports the clause in `08-discussion.tex:47`.
  The clause "level of credibility set by context of use and consequence of a wrong decision" rests on ANSI, GlobalSpec and FDA summaries; the standard's own text was not read.

The entry in `paper/acme/references-acme.bib` was already correct in title, year and number; CRP-S09 changed the url to the ASME page and added publisher and type:

```bibtex
@manual{asme2018vv40,
  author = {{American Society of Mechanical Engineers}},
  title = {{Assessing Credibility of Computational Modeling through Verification and Validation: Application to Medical Devices}},
  type = {Standard},
  number = {ASME V\&V 40-2018},
  organization = {ASME},
  publisher = {American Society of Mechanical Engineers},
  year = {2018},
  url = {https://www.asme.org/codes-standards/find-codes-standards/assessing-credibility-of-computational-modeling-through-verification-and-validation-application-to-medical-devices},
  note = {Standard; no DOI. ASME product page and FDA recognised-standards entry (recognition number 5-122) read on 2026-11-07}
}
```

## Other findings of the CRP-S09 reference run (for the lead)
- Order 148 (Han et al.): the coded DOI `10.1037/rev0000446` resolves to a different paper (Bhatia, "Inductive reasoning in minds and machines", Psychological Review 2024). The cited record is
  Han, Ransom, Perfors, Kemp, Cognitive Systems Research 83, 101155 (2024), doi 10.1016/j.cogsys.2023.101155 (arXiv 2306.06548). The extraction field A.doi of that record is wrong.
- Order 99 (Hagendorff et al.) was already in the bib as `hagendorff2023intuitive` (the published version of arXiv 2306.07622), so 3 of the 80 were present, not 2 (the others: inc088 = arXiv 2302.08399, inc145 = arXiv 2105.02987).
- Published versions found and cited instead of the preprint (Crossref): orders 24, 34, 59, 113, 126, 147, 148. Venue-only acceptances without a DOI in Crossref (arXiv comment): orders 23, 62, 73, 75, 78, 106, 117, 144, 145 are cited as the arXiv record.
- Order 49 had neither DOI nor arXiv id; resolved by title in Crossref to PsyArXiv `10.31234/osf.io/ypw5r` (Zhang, She, Gerstenberg, Rose; the CogSci 2023 proceedings version has no DOI found).
- Order 22 (Grander et al.) has a Correction notice (10.3389/frai.2026.1925443, 2026-08-07); noted in the bib entry. No retraction or withdrawal found for any of the 80.
- Order 16: Crossref truncates the title to "capabilitie"; the journal page title is used.
- DOI of order 59 (`10.18653/2026.findings-emnlp.276`) has no `v1` segment but is the Crossref-registered form and doi.org redirects it to aclanthology.org/2026.findings-emnlp.276.

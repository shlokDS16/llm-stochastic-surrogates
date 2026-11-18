import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_wordings as C  # noqa: E402


def failed(item, d, w="W4"):
    base = C.load(item, "W0")
    return [(f, r) for f, r, ok, _ in C.rules(item, d, base, w) if not ok]


def good(item, w):
    return copy.deepcopy(C.load(item, w))


# ---------------------------------------------------------------- helpers
def test_numerals_digits_fractions_commas_and_words():
    assert C.numerals("1/3 probability that 600 people, 2/3 of 5,000,000") == {"1/3", "600", "2/3", "5,000,000"}
    assert C.numerals("Two programs, all three, one 3 and two 6's") == {"two", "three", "one", "3", "6"}
    assert C.numerals("saving no one") == set()          # pronoun, not a number
    assert C.numerals("1,500 miles") == {"1,500"}        # comma form kept verbatim, 1500 is a different token
    assert C.numerals("1500 miles") == {"1500"}


def test_scale_labels_and_direction():
    assert C.scale_dir_ok("P3", "Rate from 1 (definitely stay at home) to 9 (definitely go to the game).", False) is None
    assert C.scale_dir_ok("P3", "Rate from 1 (definitely stay at home) to 9 (definitely go to the game).", True) is not None
    assert C.scale_dir_ok("P3", "Use a 9-point scale: 1 = Definitely go to the game, 9 = Definitely stay at home.", True) is None
    t = "Use a 9-point scale: 1 = Strongly agree, 5 = Neither agree nor disagree, 9 = Strongly disagree."
    assert C.scale_dir_ok("QA", t, False) is None and C.scale_dir_ok("QA", t, True) is not None


# ---------------------------------------------------------------- real files pass
def test_all_gate_checks_pass():
    rep = C.run()
    assert rep["total"]["gate_failed"] == 0, [(x["item"], x["wording"], x["gate_failed"]) for x in rep["files"] if x["gate_failed"]]
    assert rep["total"]["paraphrase_files"] == 6 * 7 + 9 * 3      # W4-W9 of 7 pilot items, W1-W9 of AF, QA, NR
    # 2 decoys per item
    assert sum(1 for x in rep["files"] if x["kind"] == "decoy") == 20


def test_file_counts():
    for item in C.ITEMS:
        for w in C.WORDINGS:
            assert C.path_of(item, w).exists(), (item, w)
        for k in (1, 2):
            assert (C.ACME / "decoys" / f"{item}_D{k}.yaml").exists()


# ---------------------------------------------------------------- mutations must fail
def test_p1_changed_numeral_fails():
    d = good("P1", "W4")
    d["frames"]["x1"]["sure"] = d["frames"]["x1"]["sure"].replace("200", "300")
    assert ("x1.sure", "numerals_equal_W0") in failed("P1", d)


def test_p1_new_number_word_and_lost_placeholder_fail():
    d = good("P1", "W4")
    d["question"] = "Which of the two programs would be chosen by you?"
    assert ("stem+question", "numerals_equal_W0") not in failed("P1", d)     # 'two' is already in the stem group
    d["question"] = "Which of the programs would be chosen by you?"
    d["stem"] = d["stem"].replace("Two alternative", "Several alternative")
    assert ("stem+question", "numerals_equal_W0") in failed("P1", d)
    d = good("P1", "W4")
    d["frames"]["x0"]["risky"] = d["frames"]["x0"]["risky"].replace("{L}", "B")
    assert ("x0.risky", "placeholder_L_once") in failed("P1", d)


def test_p1_frame_verb_swapped_fails():
    d = good("P1", "W4")
    d["frames"]["x0"]["sure"] = "If Program {L} is adopted, 400 people will be saved."
    assert ("x0.sure", "loss_verb") in failed("P1", d)


def test_p2_baseline_with_anchor_fails_and_direction_flip_fails():
    d = good("P2a", "W4")
    d["baseline"] = "Is it more than 1,500 miles from San Francisco to New York City?"
    assert ("baseline", "no_anchor_numeral") in failed("P2a", d)
    d = good("P2a", "W4")
    d["conditions"]["x1"] = d["conditions"]["x1"].replace("shorter", "longer")
    assert ("x1", "upper_bound_direction") in failed("P2a", d)
    d = good("P2b", "W5")
    d["conditions"]["x0"] = d["conditions"]["x0"].replace("200,000", "200000")
    assert ("x0", "numerals_equal_W0") in failed("P2b", d)


def test_p3_scale_not_reversed_fails():
    d = good("P3", "W4")
    d["scale_reversed"] = d["scale"]
    assert ("scale_reversed", "direction_reversed") in failed("P3", d)
    d = good("P3", "W4")
    d["scale"] = d["scale"].replace("9-point", "7-point")
    assert ("scale", "numerals_equal_W0") in failed("P3", d)


def test_af_verb_rules():
    d = good("AF", "W4")
    d["conditions"]["x1"] = d["conditions"]["x1"].replace("forbidden", "prohibited")
    assert ("x1", "verb_forbid") in failed("AF", d)
    d = good("AF", "W4")
    d["conditions"]["x0"] = d["conditions"]["x0"].replace("allowed", "forbidden")
    assert ("x0", "verb_allow") in failed("AF", d)


def test_qa_quote_and_speaker_rules():
    d = good("QA", "W4")
    d["conditions"]["x1"] = d["conditions"]["x1"].replace("only live free", "live free")
    assert ("x1", "quote_verbatim") in failed("QA", d)
    d = good("QA", "W4")
    d["conditions"]["x0"] = d["conditions"]["x0"].replace("Osama Bin Laden", "Osama bin Laden")
    assert ("x0", "speaker_bin_laden") in failed("QA", d)
    d = good("QA", "W4")
    d["scale_reversed"] = d["scale"]
    assert ("scale_reversed", "direction_reversed") in failed("QA", d)


def test_nr_roles_rules():
    d = good("NR", "W4")
    d["q_us"], d["q_other"] = d["q_other"], d["q_us"]
    f = failed("NR", d)
    assert ("q_us", "us_asks_about_nk_reporters") in f and ("q_other", "nk_asked_about_american_reporters") in f
    d = good("NR", "W4")
    d["q_us"] = d["q_us"].replace("North Korea", "Cuba")
    assert ("q_us", "us_asks_about_nk_reporters") in failed("NR", d)


def test_hygiene_and_keys():
    d = good("P4", "W4")
    d["conditions"]["x1"] = d["conditions"]["x1"] + " "
    assert ("*", "hygiene") in failed("P4", d)
    d = good("P4", "W4")
    d["extra"] = 1
    assert ("*", "keys") in failed("P4", d)


def test_decoys_change_meaning_and_carry_note():
    for item in C.ITEMS:
        base = C.load(item, "W0")
        for k in (1, 2):
            d, res = C.check_decoy(item, k, base)
            assert all(ok for _, _, ok, _ in res), (item, k, [r for r in res if not r[2]])

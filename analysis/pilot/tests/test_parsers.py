import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import parsers as P  # noqa: E402

GAIN = ["A", "B"]
LOSS = ["C", "D"]


# ------------------------------------------------------------------ choices, F0
@pytest.mark.parametrize("text,labels,expect", [
    ("A", GAIN, "A"),
    ("B.", GAIN, "B"),
    ("**B**", GAIN, "B"),
    ("(A)", GAIN, "A"),
    ("Program A", GAIN, "A"),
    ("program b", GAIN, "B"),
    ("Program C", LOSS, "C"),
    ("D\n", LOSS, "D"),
    ("  C, because it is safer", LOSS, "C"),
    ("Answer: B", GAIN, "B"),
    ("I would choose Program A.", GAIN, "A"),
    ("I choose B", GAIN, "B"),
    ("b", GAIN, "B"),
])
def test_choice_f0_valid(text, labels, expect):
    r = P.parse_choice(text, labels, "F0")
    assert r["valid"] and r["value"] == expect, r


@pytest.mark.parametrize("text,labels", [
    ("", GAIN),
    ("A person should think carefully.", GAIN),       # 'A' is an article, not a label
    ("Program C", GAIN),                                # label of the other frame
    ("C", GAIN),
    ("I cannot choose.", GAIN),
    ("I would choose Program A over Program B", GAIN),  # two labels in prose
    ("Both programs save the same expected number.", GAIN),
    ("E", GAIN),
])
def test_choice_f0_invalid(text, labels):
    r = P.parse_choice(text, labels, "F0")
    assert not r["valid"], r


# ------------------------------------------------------------------ choices, F1
def test_choice_f1_answer_line():
    t = "Program A saves 200 for sure.\nI prefer the certain outcome.\nAnswer: A"
    r = P.parse_choice(t, GAIN, "F1")
    assert r["valid"] and r["value"] == "A" and r["method"] == "answer_line"


def test_choice_f1_uses_last_marker_and_formatting():
    t = "Answer: B is tempting.\nOn balance:\n**Answer: Program A**"
    r = P.parse_choice(t, GAIN, "F1")
    assert r["valid"] and r["value"] == "A"


def test_choice_f1_no_marker_is_invalid_even_if_letter_present():
    r = P.parse_choice("I think Program A is best. A", GAIN, "F1")
    assert not r["valid"]


def test_choice_f1_wrong_frame_label():
    r = P.parse_choice("reason\nAnswer: A", LOSS, "F1")
    assert not r["valid"]


# ------------------------------------------------------------------ numbers
@pytest.mark.parametrize("text,expect", [
    ("3000", 3000.0),
    ("3,000", 3000.0),
    ("2,790 miles", 2790.0),
    ("about 2,500 miles", 2500.0),
    ("Approximately 2.7 million", 2.7e6),
    ("2.7 million.", 2.7e6),
    ("1.5k", 1500.0),
    ("30 thousand", 30000.0),
    ("**29,032**", 29032.0),
    ("$5,000", 5000.0),
    ("~ 400", 400.0),
    ("0", 0.0),
    ("12", 12.0),
    ("Answer: 8", 8.0),
    ("three", 3.0),
    ("15 times (roughly 20 including the last)", 15.0),
    ("1 000 000", 1e6),
])
def test_number_f0_valid(text, expect):
    r = P.parse_number(text, "F0")
    assert r["valid"] and r["value"] == pytest.approx(expect), r


@pytest.mark.parametrize("text", [
    "", "I don't know", "It depends on many factors.", "2,000-3,000", "2,000 to 3,000", "between 2 and 3 thousand",
    "-5", "The answer is unclear",
])
def test_number_f0_invalid(text):
    assert not P.parse_number(text, "F0")["valid"]


def test_number_range_midpoint_noted():
    r = P.parse_number("2,000 to 3,000", "F0")
    assert not r["valid"] and "midpoint=2500" in r["note"]


def test_number_f1_answer_line():
    t = "Chicago is the third largest city.\nIts metro area is larger.\nAnswer: 2,700,000"
    r = P.parse_number(t, "F1")
    assert r["valid"] and r["value"] == 2.7e6 and r["method"] == "answer_line"


def test_number_f1_last_marker_and_missing():
    assert P.parse_number("x\nAnswer: 10\ny\nAnswer: 12", "F1")["value"] == 12.0
    assert not P.parse_number("The estimate is about 3000.", "F1")["valid"]
    assert not P.parse_number("reason\nAnswer:", "F1")["valid"]


def test_number_truncated_reasoning_is_invalid():
    assert not P.parse_number("Thinking about the question, I recall that the population is roughly 2.7 mill", "F1")["valid"]


# ------------------------------------------------------------------ ratings
@pytest.mark.parametrize("text,expect", [("7", 7.0), ("9.", 9.0), ("**3**", 3.0), ("Answer: 5", 5.0), ("1", 1.0), ("6/9", 6.0), ("8 - go", 8.0)])
def test_rating_valid(text, expect):
    r = P.parse_response("rating", text, "F0")
    assert r["valid"] and r["value"] == expect, r


@pytest.mark.parametrize("text", ["0", "10", "11", "", "stay at home", "100"])
def test_rating_invalid(text):
    assert not P.parse_response("rating", text, "F0")["valid"]


def test_rating_f1():
    r = P.parse_response("rating", "It is cold but I paid.\nAnswer: 6", "F1")
    assert r["valid"] and r["value"] == 6.0


def test_dispatch_choice():
    assert P.parse_response("choice", "B", "F0", labels=GAIN)["value"] == "B"

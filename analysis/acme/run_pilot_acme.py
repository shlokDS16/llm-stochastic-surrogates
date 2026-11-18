"""analysis/pilot/run_pilot.py unchanged, with two substitutions for the ACME Arm S runs (S1, S2 on the pilot items):
model loading by analysis/acme/scoring.load (same weights and dtype; memory cap 0.88; CPU input embedding for the 13-14B models)
and a thermal pause (GPU above 87 C waits until 80 C) before each generation batch. Same arguments as run_pilot.py.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "analysis/pilot"))
import run_pilot as RP  # noqa: E402
import run_armS  # noqa: E402  (thermal_wait)
import scoring  # noqa: E402

_gen = RP.generate_safe


def _gen_cool(*a, **k):
    run_armS.thermal_wait()
    return _gen(*a, **k)


RP.load_model = scoring.load
RP.generate_safe = _gen_cool

if __name__ == "__main__":
    RP.main()

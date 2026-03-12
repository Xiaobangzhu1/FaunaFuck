from fauna.regression_targets import EXPECTED_COUNTS
from fauna.simulation.headless_runner import run_headless


def test_seed_42_regression_targets():
    actual = run_headless(max(EXPECTED_COUNTS))
    assert actual == EXPECTED_COUNTS

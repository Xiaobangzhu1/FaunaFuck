from __future__ import annotations

from .simulation.headless_runner import run_headless


EXPECTED_COUNTS = {
    100: 409,
    200: 665,
    300: 1013,
    400: 969,
    500: 950,
    600: 1020,
}


def main() -> int:
    actual = run_headless(max(EXPECTED_COUNTS))
    failed = False
    for tick, expected in EXPECTED_COUNTS.items():
        got = actual.get(tick)
        status = 'OK' if got == expected else 'FAIL'
        print(f'{status} tick={tick} expected={expected} actual={got}')
        if got != expected:
            failed = True
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())

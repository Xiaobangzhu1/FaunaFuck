from __future__ import annotations

import sys
from pathlib import Path

try:
    from .app import run as run_app
except ImportError:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from fauna.app import run as run_app


def main() -> None:
    run_app()


if __name__ == '__main__':
    main()

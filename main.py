"""SlimClaw - Entry point."""

import sys
from pathlib import Path

# Add src to path for development
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

from slimclaw.cli import Runner


def main():
    runner = Runner()
    runner.run()


if __name__ == "__main__":
    main()

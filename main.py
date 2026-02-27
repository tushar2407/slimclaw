"""SlimClaw - Entry point."""

import sys
from pathlib import Path
from slimclaw.cli import Runner

# Add src to path for development
src_path = Path(__file__).parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))


def main():
    runner = Runner()
    runner.run()


if __name__ == "__main__":
    main()

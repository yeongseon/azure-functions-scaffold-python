from pathlib import Path
import sys

from tools.verification_environment import clean, doctor
from tools.verification_evidence import report


def main() -> int:
    match sys.argv[1]:
        case "doctor":
            return doctor()
        case "clean":
            clean(Path.cwd())
            return 0
        case "report":
            return report(Path("test-results"))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

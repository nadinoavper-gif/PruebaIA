from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from xau_system.implementation import ImplementationModule


def main() -> int:
    parser = argparse.ArgumentParser(description="Checks de implementación del sistema XAU/USD")
    parser.add_argument("--api", default="http://127.0.0.1:8000", help="Base URL API para smoke test")
    parser.add_argument("--skip-api", action="store_true", help="Ejecutar solo smoke test de core")
    args = parser.parse_args()

    core = ImplementationModule.smoke_test_core()
    print(f"[CORE] ok={core.ok} detail={core.detail}")

    if args.skip_api:
        return 0 if core.ok else 1

    api = ImplementationModule.smoke_test_api(args.api)
    print(f"[API ] ok={api.ok} detail={api.detail}")

    return 0 if (core.ok and api.ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())

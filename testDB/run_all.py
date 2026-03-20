import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def run_script(script_name: str) -> int:
    script = BASE_DIR / script_name
    print(f"\n=== Running {script_name} ===", flush=True)
    result = subprocess.run([sys.executable, str(script)], cwd=str(BASE_DIR))
    return int(result.returncode)


def main() -> int:
    scripts = [
        "test_postgresql.py",
        "test_mongodb.py",
        "test_minio.py",
    ]
    summary: list[tuple[str, int]] = []

    for script_name in scripts:
        code = run_script(script_name)
        summary.append((script_name, code))

    print("\n=== Summary ===")
    has_fail = False
    for script_name, code in summary:
        if code == 0:
            status = "PASS"
        elif code == 2:
            status = "WARN"
        else:
            status = "FAIL"
            has_fail = True
        print(f"{script_name}: {status} (exit={code})")

    return 1 if has_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())

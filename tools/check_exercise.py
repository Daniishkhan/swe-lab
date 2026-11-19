#!/usr/bin/env python3
"""
Prove an exercise's tests do their job, without putting a solution in the repo.

  python3 tools/check_exercise.py sorts --pass ~/scratch/ref.py --fail ~/scratch/slow.py

Checks that:
  - the stub in the repo still raises NotImplementedError and fails its tests,
  - every --pass file (a reference solution) passes the tests,
  - every --fail file (correct but too slow, or subtly wrong) fails them.

Each solution runs in its own temp copy of the exercises folder, so nothing in
the repo changes. Solution files must live outside the repo.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_tests(folder: Path, module: str) -> tuple[int, str]:
    (folder / "pytest.ini").write_text("[pytest]\n")  # keep the repo's config out
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"test_{module}.py"],
        cwd=folder, capture_output=True, text=True,
    )
    lines = [l for l in proc.stdout.strip().splitlines() if l.strip()]
    failed = [l for l in lines if l.startswith("FAILED")]
    return proc.returncode, "\n".join(failed[:8] + lines[-1:])


def check(module: str, solution: Path | None, folder: Path, want_pass: bool) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "exercises"
        shutil.copytree(folder, work, ignore=shutil.ignore_patterns("__pycache__"))
        if solution:
            shutil.copy(solution, work / f"{module}.py")
        code, summary = run_tests(work, module)
    ok = (code == 0) == want_pass
    label = solution.name if solution else "stub"
    print(f"{'ok  ' if ok else 'FAIL'} {label}: expected {'pass' if want_pass else 'fail'}")
    print("     " + summary.replace("\n", "\n     "))
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("module", help="exercise module name, e.g. sorts")
    ap.add_argument("--pass", dest="passing", type=Path, action="append", default=[], help="solution that must pass")
    ap.add_argument("--fail", dest="failing", type=Path, action="append", default=[], help="solution that must fail")
    args = ap.parse_args()

    stubs = list(ROOT.glob(f"sections/*/exercises/{args.module}.py"))
    if len(stubs) != 1:
        sys.exit(f"Expected one sections/*/exercises/{args.module}.py, found {len(stubs)}.")
    stub = stubs[0]
    if not (stub.parent / f"test_{args.module}.py").exists():
        sys.exit(f"No test_{args.module}.py next to {stub.relative_to(ROOT)}.")
    for p in args.passing + args.failing:
        if not p.is_file():
            sys.exit(f"{p} is not a file.")
        if p.resolve().is_relative_to(ROOT):
            sys.exit(f"{p} is inside the repo. Keep solutions in a scratch folder outside it.")

    ok = True
    if "NotImplementedError" not in stub.read_text(encoding="utf-8"):
        print(f"FAIL {stub.relative_to(ROOT)} has no NotImplementedError: is a solution in the repo?")
        ok = False
    ok &= check(args.module, None, stub.parent, want_pass=False)
    for p in args.passing:
        ok &= check(args.module, p, stub.parent, want_pass=True)
    for p in args.failing:
        ok &= check(args.module, p, stub.parent, want_pass=False)
    if not args.passing:
        print("note: no --pass solution given, so only the stub was checked.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Score an agent workspace against the hidden checks.

    python3 verify.py <workspace>   # prints {task: {"score": 0..1, "detail": str}} as JSON
    python3 verify.py --self-test   # starter must score < 1, reference solutions must score 1
"""
import ast
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS, VERIFY = ROOT / "tasks", ROOT / "verify"
TIMEOUT = 60  # seconds per unittest run; an infinite loop scores 0


def run_unittest(d: Path, pattern: str) -> tuple[int, int]:
    """(passed, total) for the tests matching `pattern` in d. No tests or a timeout -> (0, 1)."""
    try:
        p = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", pattern],
                           cwd=d, capture_output=True, text=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return 0, 1
    m = re.search(r"Ran (\d+) test", p.stderr)
    total = int(m.group(1)) if m else 0
    if total == 0:
        return 0, 1
    bad = sum(int(x) for x in re.findall(r"(?:failures|errors)=(\d+)", p.stderr))
    return max(0, total - bad), total  # subTest failures can outnumber tests


def task_copy(ws: Path, task: str, tmp: str) -> Path:
    d = Path(tmp) / task
    shutil.copytree(ws / task, d, ignore=shutil.ignore_patterns("__pycache__"))
    return d


def hidden_tests(ws: Path, task: str) -> tuple[float, str]:
    with tempfile.TemporaryDirectory() as tmp:
        d = task_copy(ws, task, tmp)
        for f in (VERIFY / task / "hidden").iterdir():
            shutil.copy(f, d)
        passed, total = run_unittest(d, "test_hidden*.py")
    return passed / total, f"{passed}/{total} hidden tests"


RANDOM_TIMEOUT = 120  # seconds for all random cases; unfinished cases count as wrong


def random_inputs(ws: Path, task: str) -> tuple[float, str]:
    """Agreement with the reference solution on random inputs (verify/<task>/differential.py)."""
    reference = next((VERIFY / task / "reference").glob("*.py"))
    with tempfile.TemporaryDirectory() as tmp:
        d = task_copy(ws, task, tmp)
        shutil.copy(reference, d / "reference_impl.py")
        shutil.copy(VERIFY / task / "differential.py", d)
        try:
            out = subprocess.run([sys.executable, "differential.py"], cwd=d, capture_output=True,
                                 text=True, timeout=RANDOM_TIMEOUT).stdout
        except subprocess.TimeoutExpired as e:
            out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    lines = out.split()
    if len(lines) < 3:
        return 0.0, "random inputs: crashed before the first result"
    agree, done, total = map(int, lines[-3:])
    note = f" (timed out after {done})" if done < total else ""
    return agree / total, f"random inputs: {agree}/{total} agree{note}"


def hidden_and_random(ws: Path, task: str) -> tuple[float, str]:
    hidden, hidden_detail = hidden_tests(ws, task)
    rand, rand_detail = random_inputs(ws, task)
    return (hidden + rand) / 2, f"{hidden_detail}; {rand_detail}"


def score_tests_written(ws: Path, task: str) -> tuple[float, str]:
    spec = importlib.util.spec_from_file_location("mutants", VERIFY / task / "mutants.py")
    mutants = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mutants)
    original = (TASKS / task / "pricing.py").read_text()

    def run_with(src: str) -> tuple[int, int]:
        with tempfile.TemporaryDirectory() as tmp:
            d = task_copy(ws, task, tmp)
            (d / "pricing.py").write_text(src)
            return run_unittest(d, "test*.py")

    passed, total = run_with(original)
    if passed != total:
        return 0.0, f"own tests fail on correct code ({passed}/{total})"
    killed = [name for name, old, new in mutants.MUTANTS
              if (lambda r: r[0] < r[1])(run_with(mutants.apply(original, old, new)))]
    survived = sorted({m[0] for m in mutants.MUTANTS} - set(killed))
    return len(killed) / len(mutants.MUTANTS), f"{len(killed)}/{len(mutants.MUTANTS)} mutants caught; survived: {survived}"


def score_refactor(ws: Path, task: str) -> tuple[float, str]:
    behaviour, detail = hidden_tests(ws, task)
    files = sorted((ws / task / "shop").glob("*.py"))
    old_name_gone = not any("fmt_money" in f.read_text() for f in files)
    funcs = [n for f in files for n in ast.walk(ast.parse(f.read_text()))
             if isinstance(n, ast.FunctionDef) and (not n.name.startswith("_") or n.name == "__init__")]

    def annotated(fn: ast.FunctionDef) -> bool:
        args = fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs
        return fn.returns is not None and all(a.annotation for a in args if a.arg not in ("self", "cls"))

    typed = sum(map(annotated, funcs)) / len(funcs)
    documented = sum(ast.get_docstring(fn) is not None for fn in funcs) / len(funcs)
    score = (behaviour + old_name_gone + typed + documented) / 4
    return score, f"{detail}; old name gone={old_name_gone}; typed={typed:.0%}; docstrings={documented:.0%}"


PLANTED = {"get_user", "download_file", "run_report", "load_session", "hash_password"}
FP_PENALTY = 0.1


def score_review(ws: Path, task: str) -> tuple[float, str]:
    tree = ast.parse((TASKS / task / "app.py").read_text())  # original line numbers
    spans = {n.name: (n.lineno, n.end_lineno) for n in tree.body if isinstance(n, ast.FunctionDef)}
    findings = json.loads((ws / task / "findings.json").read_text())
    hits, false_pos = set(), []
    for f in findings:
        line = int(f["line"])
        fn = next((name for name, (a, b) in spans.items() if a <= line <= b), None)
        if fn in PLANTED:
            hits.add(fn)  # a second finding in the same planted function is tolerated
        else:
            false_pos.append(f"{line}:{fn}")
    score = max(0.0, len(hits) / len(PLANTED) - FP_PENALTY * len(false_pos))
    return score, f"{len(hits)}/{len(PLANTED)} found; false positives: {false_pos}"


SCORERS = {
    "01-bugfix": hidden_tests,
    "02-write-tests": score_tests_written,
    "03-refactor": score_refactor,
    "04-feature": hidden_and_random,
    "05-cron": hidden_and_random,
    "06-security-review": score_review,
    "07-root-cause": hidden_tests,
    "08-concurrency": hidden_tests,
    "09-api-migration": hidden_tests,
    "10-datetime-migration": hidden_tests,
    "11-envfile": hidden_tests,
    "12-stock-drift": hidden_tests,
    "13-config-v2": hidden_tests,
}


def score_workspace(ws: Path) -> dict:
    out = {}
    for task, scorer in SCORERS.items():
        if not (ws / task).is_dir():
            continue  # subset run
        try:
            score, detail = scorer(ws, task)
        except Exception as e:  # broken output (syntax error, missing file) scores 0
            score, detail = 0.0, f"error: {type(e).__name__}: {e}"
        out[task] = {"score": round(score, 3), "detail": detail}
    return out


def self_test() -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        starter, ref = Path(tmp) / "starter", Path(tmp) / "ref"
        shutil.copytree(TASKS, starter)
        shutil.copytree(TASKS, ref)
        for task in SCORERS:
            if (VERIFY / task / "reference").is_dir():
                shutil.copytree(VERIFY / task / "reference", ref / task, dirs_exist_ok=True)
            deletions = VERIFY / task / "reference_delete.txt"  # files the reference solution removes
            for name in deletions.read_text().split() if deletions.exists() else []:
                (ref / task / name).unlink()
        s, r = score_workspace(starter), score_workspace(ref)
    ok = True
    for task in SCORERS:
        good = r[task]["score"] == 1 and s[task]["score"] < 1
        ok &= good
        print(f"{'ok ' if good else 'BAD'} {task:20} starter={s[task]['score']:.2f} reference={r[task]['score']:.2f}"
              f"  | {r[task]['detail']}")
    return ok


if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        sys.exit(0 if self_test() else 1)
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(json.dumps(score_workspace(Path(sys.argv[1])), indent=2))

"""Exercise the authored submission fixtures through both container images."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--duel", action="store_true")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
rows = []
fixtures = sorted((root / "adversarial").glob("*.py"))
for fixture in fixtures:
    output = root / "evidence" / "adversarial" / fixture.stem
    cmd = [sys.executable, str(root / "scripts/docker_match.py"), "--submission", str(fixture),
           "--episodes", "256", "--output", str(output)]
    if args.duel:
        cmd += ["--referee-image", "cmm-referee:dev"]
        for _ in range(3):
            cmd += ["--submission", str(root / "player/submission.py")]
    completed = subprocess.run(cmd, cwd=root, capture_output=True, text=True, timeout=1300)
    if completed.returncode:
        raise RuntimeError(completed.stderr[-3000:])
    run = json.loads((output / "run.json").read_text())
    result = run["result"]
    assert result["raw_scores"][0] <= 0, (fixture.name, result)
    rows.append({"submission": fixture.name, "scores": result["raw_scores"],
                 "winner": result["winner"], "terminal_reason": result["terminal_reason"],
                 "seconds": result["metadata"]["elapsed_s"]})
    (root / "evidence/adversarial-results.json").write_text(json.dumps(rows, indent=2) + "\n")
    print(fixture.name, result["raw_scores"], flush=True)

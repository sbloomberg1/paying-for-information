"""Trusted reference-policy experiments. Run submissions in containers instead."""
import argparse
from dataclasses import asdict
import importlib.util
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "referee"))
from referee import evaluate
from market import Episode


class Local:
    def __init__(self, mode="adaptive"):
        path = ROOT / ("benchmarks/overfit.py" if mode == "overfit" else "player/submission.py")
        spec = importlib.util.spec_from_file_location("baseline", path)
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.module
        spec.loader.exec_module(self.module)
        self.module.MODE = mode

    def reset(self, config):
        self.module.reset(config)

    def act(self, observation, deadline_ms):
        return self.module.act(observation)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--episodes", type=int, default=2048)
    parser.add_argument("--modes", nargs="+", default=["adaptive", "never", "periodic", "always", "overfit"])
    parser.add_argument("--duel", action="store_true")
    parser.add_argument("--stress", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = []
    if args.duel and len(args.modes) != 4:
        parser.error("duel requires four modes")
    for seed in range(args.seeds):
        for name in (["field"] if args.duel else args.modes):
            modes = args.modes if args.duel else [name]
            result = evaluate(seed, [Local(m) for m in modes], {"episodes": args.episodes},
                              mode="duel" if args.duel else "solo", stress=args.stress)
            rows.append({"sample": seed, "policy": name, **asdict(result)})
            print(json.dumps({"sample": seed, "policy": name, "scores": result.raw_scores,
                              "seconds": result.metadata["elapsed_s"]}), flush=True)
        Path(args.output).write_text(json.dumps({"episodes": args.episodes, "modes": args.modes,
                                                "stress": args.stress, "rows": rows}, indent=2) + "\n")
    for name in (["field"] if args.duel else args.modes):
        scores = [r["raw_scores"][0] for r in rows if r["policy"] == name]
        mean = statistics.mean(scores)
        sd = statistics.stdev(scores) if len(scores) > 1 else 0
        print(name, "mean", mean, "round_sd", sd, "quarter_margin", mean * 0.0025)


if __name__ == "__main__":
    main()

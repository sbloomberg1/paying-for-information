"""Verify episode accounting and aggregate results from an evaluation artifact."""
import argparse
import gzip
import json
from pathlib import Path


def read(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    totals = None
    episodes = 0
    summary = None
    identities = set()
    with opener(path, "rt") as stream:
        for line in stream:
            record = json.loads(line)
            if record["format"] == "market-summary-v1":
                summary = record
                continue
            if record["format"] != "market-episode-v1" or summary is not None:
                raise ValueError("unexpected record")
            if record["episode"] in identities:
                raise ValueError("duplicate episode")
            identities.add(record["episode"])
            if totals is None:
                totals = [0] * len(record["active"])
            for seat, account in enumerate(record["accounts"]):
                cash, position, edge, costs = 1_000_000, 0, 0, 0
                for turn in record["turns"]:
                    cost = turn["information_delta"][seat]
                    cash -= cost
                    edge -= cost
                    costs += cost
                    for fill in turn["fills"][seat]:
                        change = fill["side"] * fill["quantity"]
                        position += change
                        cash -= change * fill["price"]
                        edge += change * (turn["fair"] - fill["price"])
                assert (cash, position, edge, costs) == (account["cash"], account["inventory"],
                                                       account["edge_ticks"], account["information_ticks"])
                assert cash + position * record["terminal_fair"] - 1_000_000 == account["terminal_profit_ticks"]
                if seat < len(totals):
                    totals[seat] += edge
            episodes += 1
    if summary is None:
        raise ValueError("summary unavailable")
    totals = totals or [0] * len(summary["active"])
    assert episodes == summary["completed"]
    assert [v / (summary["requested"] * 10_000) for v in totals] == summary["signed_edge"]
    active = summary["active"]
    if len(active) == 1:
        expected = [max(0.0, summary["signed_edge"][0]) if active[0] else 0.0]
        winner = 0 if expected[0] > 0 else -1
    else:
        expected = [summary["signed_edge"][i] if active[i] else -1000.0 for i in range(len(active))]
        eligible = [i for i in range(len(active)) if active[i]]
        best = max((totals[i] for i in eligible), default=None)
        leaders = [i for i in eligible if totals[i] == best]
        winner = leaders[0] if len(leaders) == 1 else -1
    assert summary["scores"] == expected and summary["winner"] == winner
    return {"episodes_verified": episodes, "scores": summary["scores"], "winner": summary["winner"],
            "active": summary["active"], "compressed_bytes": Path(path).stat().st_size}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    print(json.dumps(read(parser.parse_args().path), indent=2))

from __future__ import annotations
from dataclasses import asdict
import gzip
import json
from pathlib import Path
import time
from gym_v1.referee import GameResult, RefereeContext
from transport import Client, PlayerFault
from market import Episode, HORIZON, SCALE, reference_quote, validate_action

MODE = "solo"


class Records:
    def __init__(self, path=None):
        self.path = Path(path) if path else None
        self.available = self.path is not None
        if self.path:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_bytes(b"")
            except OSError:
                self.available = False

    def write(self, record):
        if self.available:
            try:
                opener = gzip.open if self.path.suffix == ".gz" else open
                with opener(self.path, "at") as stream:
                    stream.write(json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n")
            except OSError:
                self.available = False


def parameters(config):
    if not isinstance(config, dict) or set(config) - {"episodes", "batch_size", "deadline_ms"}:
        raise ValueError("invalid round input")
    values = {"episodes": 32768, "batch_size": 512, "deadline_ms": 100} | config
    if any(type(v) is not int for v in values.values()):
        raise ValueError("invalid round input")
    if values["episodes"] not in (256, 2048, 8192, 32768) or values["batch_size"] != 512:
        raise ValueError("invalid round input")
    if values["deadline_ms"] != 100:
        raise ValueError("invalid round input")
    return values


def evaluate(master, clients, config=None, records=None, mode="solo", stress=False):
    started = time.monotonic()
    cfg = parameters(config or {})
    count = len(clients)
    if count != (1 if mode == "solo" else 4):
        raise ValueError("invalid player count")
    records = records or Records()
    live, totals, wealth = [True] * count, [0] * count, [0] * count
    fees, volumes = [0] * count, [0] * count
    purchases = [[0] * 4 for _ in clients]
    strata = [[0] * 8 for _ in clients]
    faults = [None] * count
    completed = 0
    step_count = 0
    for seat, client in enumerate(clients):
        try:
            client.reset({"mode": mode, "horizon": HORIZON, "price_scale": SCALE,
                          "batch_size": cfg["batch_size"], "deadline_ms": cfg["deadline_ms"]})
        except PlayerFault:
            live[seat], faults[seat] = False, {"episode": 0, "tick": 0, "phase": "reset"}
    for offset in range(0, cfg["episodes"], cfg["batch_size"]):
        if not any(live):
            break
        episodes = [Episode(master, i, count + (mode == "solo"), stress)
                    for i in range(offset, min(offset + cfg["batch_size"], cfg["episodes"]))]
        histories = [[] for _ in episodes] if records.available else None
        for tick in range(HORIZON):
            previous_fees = [[a.information for a in ep.accounts] for ep in episodes]
            buys = [[0] * len(episodes) for _ in clients]
            signals = [[None] * len(episodes) for _ in clients]
            quotes = [[None] * len(episodes) for _ in clients]
            snapshots = [[None] * len(episodes) for _ in clients]
            buy_snapshots = [[None] * len(episodes) for _ in clients]
            for phase in (["buy", "quote"] if mode == "solo" else ["quote"]):
                for seat, client in enumerate(clients):
                    if not live[seat]:
                        continue
                    obs = {"phase": phase, "episodes": [ep.observation(seat, signals[seat][j], buys[seat][j])
                                                         for j, ep in enumerate(episodes)]}
                    if phase == "quote":
                        snapshots[seat] = obs["episodes"]
                    else:
                        buy_snapshots[seat] = obs["episodes"]
                    try:
                        action = validate_action(phase, client.act(obs, cfg["deadline_ms"]), len(episodes))
                        if phase == "buy":
                            buys[seat] = action
                            for j, ep in enumerate(episodes):
                                signals[seat][j] = ep.buy(seat, action[j])
                        else:
                            quotes[seat] = action
                    except (PlayerFault, ValueError):
                        live[seat] = False
                        faults[seat] = {"episode": offset, "tick": tick, "phase": phase}
                        quotes[seat] = [None] * len(episodes)
            for j, ep in enumerate(episodes):
                actions = [quotes[seat][j] if live[seat] else None for seat in range(count)]
                if mode == "solo":
                    actions.append(reference_quote(ep.observation(count)))
                first = (ep.id // 8 + tick) % len(actions)
                priority = list(range(first, len(actions))) + list(range(first))
                ep.advance(actions, priority)
                if histories is not None:
                    histories[j].append({"tick": tick, "observations": [s[j] for s in snapshots],
                                         "buy_observations": [s[j] for s in buy_snapshots],
                                         "buys": [b[j] for b in buys], "quotes": actions,
                                         "active": live[:], "fair": ep.events[tick]["fair"],
                                         "information_delta": [a.information - previous_fees[j][i]
                                                               for i, a in enumerate(ep.accounts)],
                                         "fills": [a.fills[:] for a in ep.accounts]})
            step_count += len(episodes)
            if not any(live):
                break
        for j, ep in enumerate(episodes):
            result = ep.result()
            for seat, a in enumerate(ep.accounts[:count]):
                totals[seat] += a.edge
                wealth[seat] += result["accounts"][seat]["terminal_profit_ticks"]
                fees[seat] += a.information
                volumes[seat] += a.volume
                strata[seat][ep.conditions["stratum"]] += a.edge
                for t in range(4):
                    purchases[seat][t] += a.purchases[t]
            records.write({"format": "market-episode-v1", "mode": mode, **result,
                           "turns": histories[j] if histories is not None else [], "active": live[:]})
        completed += len(episodes)
    denominator = cfg["episodes"] * SCALE
    signed = [v / denominator for v in totals]
    if mode == "solo":
        scores = [max(0.0, signed[0]) if live[0] else 0.0]
        winner = 0 if scores[0] > 0 else -1
    else:
        scores = [signed[i] if live[i] else -1000.0 for i in range(count)]
        eligible = [i for i in range(count) if live[i]]
        best = max((totals[i] for i in eligible), default=None)
        leaders = [i for i in eligible if totals[i] == best]
        winner = leaders[0] if len(leaders) == 1 else -1
    records.write({"format": "market-summary-v1", "requested": cfg["episodes"],
                   "completed": completed, "faults": faults, "active": live,
                   "signed_edge": signed, "scores": scores, "winner": winner})
    return GameResult(raw_scores=scores, winner=winner,
                      terminal_reason="completed" if all(live) else "forfeit",
                      steps=step_count,
                      metadata={"episodes": cfg["episodes"], "completed_episodes": completed,
                                "active": live, "signed_edge": signed,
                                "terminal_profit": [v / denominator for v in wealth],
                                "information_spent": [v / denominator for v in fees],
                                "volume": volumes, "purchases": purchases,
                                "stratum_edge": [[v * 8 / denominator for v in row] for row in strata],
                                "elapsed_s": round(time.monotonic() - started, 4)})


def main():
    ctx = RefereeContext.from_env()
    if ctx.num_players != len(ctx.player_urls):
        raise ValueError("invalid player count")
    result = evaluate(ctx.seed, [Client(url) for url in ctx.player_urls], ctx.config,
                      Records("/data/history/episodes.jsonl.gz"), mode=MODE)
    Path("/data/result.json").write_text(json.dumps(asdict(result), allow_nan=False) + "\n")


if __name__ == "__main__":
    main()

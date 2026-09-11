"""Discrete-time market and integer accounting, engine version 0.1.0."""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import random

SCALE = 10_000
CAPITAL = 1_000_000
POSITION_LIMIT = 20
MAX_SIZE = 4
HORIZON = 24


def derived_seed(master: int, index: int) -> int:
    return int.from_bytes(hashlib.sha256(f"market-v1:{master}:{index}".encode()).digest(), "big")


@dataclass
class Account:
    cash: int = CAPITAL
    inventory: int = 0
    edge: int = 0
    information: int = 0
    volume: int = 0
    purchases: list[int] = field(default_factory=lambda: [0, 0, 0, 0])
    fills: list[dict] = field(default_factory=list)

    def spend(self, cost: int, tier: int) -> bool:
        if min(self.cash, self.cash + self.inventory * SCALE) < cost:
            return False
        self.cash -= cost
        self.edge -= cost
        self.information += cost
        self.purchases[tier] += 1
        return True

    def fill(self, side: int, price: int, fair: int) -> bool:
        position = self.inventory + side
        cash = self.cash - side * price
        if abs(position) > POSITION_LIMIT or min(cash, cash + position * SCALE) < 0:
            return False
        self.cash, self.inventory = cash, position
        self.edge += side * (fair - price)
        self.volume += 1
        self.fills.append({"side": side, "price": price, "quantity": 1})
        return True


class Episode:
    def __init__(self, master: int, index: int, players: int, stress: bool = False):
        self.id, self.tick = index, 0
        self.accounts = [Account() for _ in range(players)]
        self.book = []
        r = random.Random(derived_seed(master, index))
        stratum = index % 8
        vol = (55 if stratum & 1 == 0 else 170) + r.randint(-10, 10)
        public_noise = (180 if stratum & 2 == 0 else 650) + r.randint(-25, 25)
        multiplier = (1 if stratum & 4 == 0 else 6)
        if stress:
            vol, public_noise, multiplier = vol * 2, public_noise * 2, multiplier * 2
        self.conditions = {"stratum": stratum, "volatility": vol,
                           "public_noise": public_noise, "information_multiplier": multiplier,
                           "retail_orders": r.choice([3, 4, 5])}
        self.costs = [0, 20 * multiplier, 65 * multiplier, 210 * multiplier]
        self.noises = [0, 300, 100, 25]
        self.events = []
        fair = r.randint(3500, 6500)
        public = fair
        for t in range(HORIZON):
            if t % 4 == 0:
                public = max(1, min(SCALE - 1, fair + r.randint(-public_noise, public_noise)))
            signals = [None] + [max(1, min(SCALE - 1, fair + r.randint(-n, n))) for n in self.noises[1:]]
            step = vol * (4 if r.random() < 0.08 else 1)
            step = min(step, fair - 1, SCALE - 1 - fair)
            next_fair = fair + r.choice([-step, step])
            retail = [(r.choice([-1, 1]), r.randint(250, 1100))
                      for _ in range(self.conditions["retail_orders"])]
            self.events.append({"fair_before": fair, "fair": next_fair, "public": public,
                                "signals": signals, "retail": retail})
            fair = next_fair
        self.terminal_fair = fair

    def observation(self, seat: int, signal: int | None = None, tier: int = 0) -> dict:
        a, e = self.accounts[seat], self.events[self.tick]
        return {"id": self.id, "tick": self.tick, "remaining": HORIZON - self.tick,
                "public": e["public"], "public_age": self.tick % 4,
                "public_noise": self.conditions["public_noise"],
                "volatility": self.conditions["volatility"],
                "signal": signal, "tier": tier, "costs": self.costs,
                "signal_noise": self.noises, "cash": a.cash, "inventory": a.inventory,
                "fills": list(a.fills), "book": self.book,
                "position_limit": POSITION_LIMIT, "max_size": MAX_SIZE}

    def buy(self, seat: int, tier: int) -> int | None:
        if not self.accounts[seat].spend(self.costs[tier], tier):
            raise ValueError("action unavailable")
        return self.events[self.tick]["signals"][tier]

    def advance(self, quotes: list[dict | None], priority: list[int]) -> None:
        e = self.events[self.tick]
        p = e["fair"]
        for a in self.accounts:
            a.fills = []
        remaining = [{"bid_size": q["bid_size"], "ask_size": q["ask_size"]} if q else
                     {"bid_size": 0, "ask_size": 0} for q in quotes]
        rank = {seat: i for i, seat in enumerate(priority)}

        def trade(buy: bool, limit: int, quantity: int):
            side, size, sign = ("ask", "ask_size", -1) if buy else ("bid", "bid_size", 1)
            order = sorted((i for i, q in enumerate(quotes) if q),
                           key=lambda i: ((quotes[i][side] if buy else -quotes[i][side]), rank[i]))
            for i in order:
                price = quotes[i][side]
                if (buy and price > limit) or (not buy and price < limit):
                    break
                while quantity and remaining[i][size]:
                    remaining[i][size] -= 1
                    if self.accounts[i].fill(sign, price, p):
                        quantity -= 1
                if not quantity:
                    break

        trade(True, p - 5, MAX_SIZE * len(quotes))
        trade(False, p + 5, MAX_SIZE * len(quotes))
        for direction, markup in e["retail"]:
            trade(direction == 1, min(SCALE, p + markup) if direction == 1 else max(0, p - markup), 1)
        self.book = [{"seat": i, **q, **remaining[i]} for i, q in enumerate(quotes) if q]
        self.tick += 1

    def result(self) -> dict:
        return {"episode": self.id, "conditions": self.conditions,
                "terminal_fair": self.terminal_fair,
                "accounts": [{"cash": a.cash, "inventory": a.inventory,
                              "edge_ticks": a.edge, "information_ticks": a.information,
                              "volume": a.volume, "purchases": a.purchases,
                              "terminal_profit_ticks": a.cash + a.inventory * self.terminal_fair - CAPITAL}
                             for a in self.accounts]}


def validate_action(phase: str, value, count: int) -> list:
    if not isinstance(value, list) or len(value) != count:
        raise ValueError("invalid action")
    for q in value:
        if phase == "buy":
            if type(q) is not int or not 0 <= q <= 3:
                raise ValueError("invalid action")
        elif q is not None:
            if not isinstance(q, dict) or set(q) != {"bid", "ask", "bid_size", "ask_size"}:
                raise ValueError("invalid action")
            if any(type(v) is not int for v in q.values()):
                raise ValueError("invalid action")
            if not (0 <= q["bid"] < q["ask"] <= SCALE and
                    0 <= q["bid_size"] <= MAX_SIZE and 0 <= q["ask_size"] <= MAX_SIZE):
                raise ValueError("invalid action")
    return value


def reference_quote(observation: dict) -> dict:
    mid = observation["public"] - 18 * observation["inventory"]
    width = 250 + observation["public_noise"] // 2 + observation["public_age"] * observation["volatility"] // 2
    return {"bid": max(0, min(9998, mid - width)), "ask": max(1, min(10000, mid + width)),
            "bid_size": 3, "ask_size": 3}

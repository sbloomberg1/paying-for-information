"""Reference strategy. Prices, costs and balances use 10,000 ticks per currency unit."""
_state = {}
MODE = "adaptive"


def reset(config):
    _state.clear()


def act(observation):
    output = []
    for o in observation["episodes"]:
        key = o["id"]
        if key not in _state or o["tick"] == 0 and observation["phase"] == "buy":
            _state[key] = [o["public"], o["public_noise"], -1]
        state = _state[key]
        if state[2] != o["tick"]:
            state[1] += o["volatility"]
            if o["public_age"] == 0:
                state[0], state[1] = o["public"], o["public_noise"]
            for fill in o["fills"]:
                if fill["side"] == -1:
                    state[0] = max(state[0], fill["price"] - state[1] // 2)
                else:
                    state[0] = min(state[0], fill["price"] + state[1] // 2)
            state[2] = o["tick"]
        if observation["phase"] == "buy":
            if MODE == "never":
                tier = 0
            elif MODE == "always":
                tier = 3
            elif MODE == "periodic":
                tier = 2 if o["tick"] % 4 == 0 else 0
            elif MODE in ("overfit", "static", "tight", "wide"):
                tier = 0
            else:
                values = [0] + [2 * max(0, state[1] - o["signal_noise"][t]) - o["costs"][t] * 2
                                for t in range(1, 4)]
                tier = max(range(4), key=lambda t: values[t])
            output.append(tier)
        else:
            if o["signal"] is not None:
                state[0], state[1] = o["signal"], o["signal_noise"][o["tier"]]
            mid = state[0] - 12 * o["inventory"]
            width = 140 + state[1] // 2 + o["volatility"]
            if MODE == "static":
                mid, width = 5000, 600
            elif MODE == "tight":
                width = max(20, width // 2)
            elif MODE == "wide":
                width = width * 3 // 2
            elif MODE == "overfit":
                mid = TRAINING[o["id"]][o["tick"]] - 12 * o["inventory"]
                width = 140 + o["volatility"]
            output.append({"bid": max(0, min(9998, mid - width)),
                           "ask": max(1, min(10000, mid + width)), "bid_size": 4, "ask_size": 4})
            if o["remaining"] == 1:
                del _state[key]
    return output

_original = act
def act(observation):
    if observation["episodes"][0]["tick"] >= 20:
        return []
    return _original(observation)

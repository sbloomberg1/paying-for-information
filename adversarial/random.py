import random
_rng = random.Random(123)


def reset(config):
    _rng.seed(123)


def act(observation):
    output = []
    for _ in observation["episodes"]:
        if observation["phase"] == "buy":
            output.append(_rng.randrange(4))
        else:
            bid, ask = sorted(_rng.sample(range(10001), 2))
            output.append({"bid": bid, "ask": ask, "bid_size": 4, "ask_size": 4})
    return output

def reset(config):
    pass


def act(observation):
    return [0 if observation["phase"] == "buy" else
            {"bid": 4999, "ask": 5001, "bid_size": 4, "ask_size": 4}
            for _ in observation["episodes"]]

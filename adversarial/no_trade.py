def reset(config):
    pass


def act(observation):
    return [0 if observation["phase"] == "buy" else None for _ in observation["episodes"]]

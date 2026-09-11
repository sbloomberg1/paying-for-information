import argparse
import importlib.util
import sys
from gym_v1.player import Player, serve


class MarketPlayer(Player):
    def __init__(self):
        spec = importlib.util.spec_from_file_location("submission", "/app/submission.py")
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.module
        spec.loader.exec_module(self.module)

    def reset(self, match_id, player_index, seed, config):
        self.module.reset(config)

    def act(self, observation, deadline_ms):
        return self.module.act(observation)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    serve(MarketPlayer(), port=args.port)

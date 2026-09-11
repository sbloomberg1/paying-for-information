import copy
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "referee"), str(ROOT / "scripts")]
from market import Account, CAPITAL, Episode, HORIZON, SCALE, validate_action
from referee import evaluate, Records, parameters
from transport import PlayerFault
from experiment import Local
from read_records import read


def test_account_and_bankruptcy():
    a = Account()
    assert a.fill(1, 4200, 5000)
    assert a.fill(-1, 5400, 5100)
    assert a.spend(200, 2)
    assert (a.cash - CAPITAL, a.inventory, a.edge) == (1000, 0, 900)
    b = Account(cash=0)
    assert not b.fill(1, 1, 5000)
    assert not b.fill(-1, 9999, 5000)
    assert not b.spend(1, 1)


@pytest.mark.parametrize("action", [{}, [None, None], [True], [float("nan")], [-1], [4]])
def test_buy_validation(action):
    with pytest.raises(ValueError):
        validate_action("buy", action, 1)


@pytest.mark.parametrize("q", [{}, {"bid": 0, "ask": 0, "bid_size": 1, "ask_size": 1},
                                 {"bid": False, "ask": 5, "bid_size": 1, "ask_size": 1},
                                 {"bid": 1, "ask": 5, "bid_size": 5, "ask_size": 1},
                                 {"bid": 1, "ask": float("inf"), "bid_size": 1, "ask_size": 1}])
def test_quote_validation(q):
    with pytest.raises(ValueError):
        validate_action("quote", [q], 1)


def test_priority_and_account_conservation():
    a, b = Episode(7, 0, 4), Episode(7, 0, 4)
    quotes = [{"bid": 4300 + i * 10, "ask": 4700 + i * 10, "bid_size": 3, "ask_size": 3}
              for i in range(4)]
    permutation = [2, 0, 3, 1]
    for _ in range(HORIZON):
        a.advance(quotes, [0, 1, 2, 3])
        b.advance([quotes[i] for i in permutation], [permutation.index(i) for i in range(4)])
    assert [a.accounts[i] for i in permutation] == b.accounts
    for account in a.accounts:
        assert abs(account.inventory) <= 20
        assert min(account.cash, account.cash + account.inventory * SCALE) >= 0


def test_future_independent_of_actions_and_observation_is_detached():
    a, b = Episode(1, 0, 2), Episode(1, 0, 2)
    event = copy.deepcopy(b.events)
    a.buy(0, 3)
    a.advance([None, None], [0, 1])
    assert a.events == event
    observation = a.observation(0)
    assert not {"seed", "fair", "fair_before", "terminal_fair", "events"} & set(observation)


def test_record_reconstructs_score_and_write_failure_neutral(tmp_path):
    recorded = evaluate(4, [Local()], {"episodes": 256}, Records(tmp_path / "records.gz"))
    no_records = evaluate(4, [Local()], {"episodes": 256}, Records(tmp_path))
    assert recorded.raw_scores == no_records.raw_scores
    assert read(tmp_path / "records.gz")["scores"] == recorded.raw_scores
    assert recorded.raw_scores[0] > 0


class LateFailure(Local):
    def act(self, observation, deadline_ms):
        if observation["episodes"][0]["tick"] >= 20:
            raise PlayerFault("player unavailable")
        return super().act(observation, deadline_ms)


def test_late_failure_has_no_partial_credit():
    result = evaluate(2, [LateFailure()], {"episodes": 256})
    assert result.raw_scores == [0]
    assert result.winner == -1
    assert result.metadata["signed_edge"][0] > 0


class Absent:
    def reset(self, config):
        raise PlayerFault("player unavailable")


def test_all_forfeit_and_partial_duel():
    result = evaluate(2, [Absent()] * 4, {"episodes": 256}, mode="duel")
    assert result.winner == -1 and result.raw_scores == [-1000] * 4
    result = evaluate(2, [Local(), Absent(), Absent(), Absent()], {"episodes": 256}, mode="duel")
    assert result.winner == 0 and result.raw_scores[1:] == [-1000] * 3


def test_round_configuration_is_bounded():
    with pytest.raises(ValueError):
        parameters({"episodes": 0})
    with pytest.raises(ValueError):
        parameters({"seed": 0})
    with pytest.raises(ValueError):
        parameters({"deadline_ms": 500})

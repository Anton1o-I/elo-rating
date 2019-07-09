import json
from typing import List
from math import ceil


def elo_adjust(outcomes: json, current) -> List[dict]:
    """
    Takes in a score dictionary (must be len 2) in the format {key:value, key:value} where key is name
    for each player and value is their score in the game
    Ex. {"p1_name": "Brian", "p1_score": 0, "p2_name": "Tyler", "p2_score": 11}
    """
    p1_rating = current["p1_current"]
    p2_rating = current["p2_current"]
    elo_diff_1 = p1_rating - p2_rating
    elo_diff_2 = p2_rating - p1_rating
    mov = abs((int(outcomes["p1_score"]) - int(outcomes["p2_score"])))
    mov1 = (mov ** 0.8) / (7.5 + 0.006 * elo_diff_1)
    mov2 = (mov ** 0.8) / (7.5 + 0.006 * elo_diff_2)
    exp1 = 1 / (1 + 10 ** ((p2_rating - p1_rating) / 400))
    exp2 = 1 / (1 + 10 ** ((p1_rating - p2_rating) / 400))
    p1_vic = 1 if int(outcomes["p1_score"]) > int(outcomes["p2_score"]) else 0
    p2_vic = 1 if int(outcomes["p2_score"]) > int(outcomes["p1_score"]) else 0
    print(exp1, p1_vic, exp2, p2_vic)
    player_updates = [
        {
            "name": outcomes["player1"],
            "rating": int(round(max(100, p1_rating + 13 * mov1 * (p1_vic - exp1)), 0)),
            "win": (1 if int(outcomes["p1_score"]) > int(outcomes["p2_score"]) else 0),
        },
        {
            "name": outcomes["player2"],
            "rating": int(round(max(100, p2_rating + 13 * mov2 * (p2_vic - exp2)), 0)),
            "win": 1 if int(outcomes["p2_score"]) > int(outcomes["p1_score"]) else 0,
        },
    ]
    return player_updates


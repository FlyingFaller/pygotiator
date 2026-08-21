from template import Move, RoundResult, RPSTemplate
import random

class MyBot(RPSTemplate):
    def make_move(self, history) -> Move:
        return random.choice([Move.ROCK, Move.PAPER, Move.SCISSORS])

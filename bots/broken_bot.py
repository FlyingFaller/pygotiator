# This bot is just for testing error handling

from template import Move, RoundResult, RPSTemplate
import random, time

class BrokenBot(RPSTemplate):
    def make_move(self, history: list[RoundResult]) -> Move:
        move_int = random.randint(1, 6)
        match move_int:
            case 1:
                return Move.ROCK
            case 2:
                return Move.PAPER
            case 3: 
                return Move.SCISSORS
            case 4:
                print('In sleep case!')
                time.sleep(30)
                return random.choice([Move.ROCK, Move.PAPER, Move.SCISSORS])
            case 5:
                return None
            case 6:
                assert False, "Test error in bot!"
            case _:
                return None

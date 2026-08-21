from template import Move, RoundResult, RPSTemplate
import random 

class Tit4TatBot(RPSTemplate):
    win_conditions = {
                    Move.SCISSORS: Move.ROCK,
                    Move.ROCK: Move.PAPER,
                    Move.PAPER: Move.SCISSORS
                }

    def random_move(self):
        return random.choice([Move.ROCK, Move.PAPER, Move.SCISSORS])
    
    def make_move(self, history: list[RoundResult]) -> Move:
        if history:
            last_result: RoundResult = history[-1]
            return self.win_conditions.get(last_result.opponent_move, self.random_move())
        else:
            return self.random_move()

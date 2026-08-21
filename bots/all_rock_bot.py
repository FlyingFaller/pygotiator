from template import Move, RoundResult, RPSTemplate

class AllRockBot(RPSTemplate):
    def make_move(self, history: list[RoundResult]) -> Move:
        return Move.ROCK

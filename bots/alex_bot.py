from template import Move, RoundResult, RPSTemplate
import random
from bots.BenBot import BenBot

# import claude
# import copilot
# import chat
# import chatgpt


class AlexBot(RPSTemplate):
    def __init__(self):
        self.ben_bot = BenBot()

    def make_move(self, history: list[RoundResult]) -> Move:
        roundNumber = len(history)

        """
        There are three pertinent categories of note, each continuously
        tracking the contents of the last ten rounds: How many rocks are in
        the pile, how many pieces of paper are in the stack, and how many
        scissors are in the bin.
        """
        pile = self.get_weight(Move.ROCK, history)
        stack = self.get_weight(Move.PAPER, history)
        bin = self.get_weight(Move.SCISSORS, history)

        """
        The contents of these categories are also weighted relative to how
        recently they were played. For example, a rock played just the
        previous turn will weigh significantly more than a rock played nine
        turns ago (erosion). This is also true for paper (sweat) and scissors
        (improper use over time).

        If at any point the contents of one of these categories reaches or
        exceeds a threshold (25 grams), then it is only logical to play the
        counter to that for every turn until the category "settles down." Of
        course, encoding this deterministic of a strategy into my bot is not
        ideal, so I will make the bot only do this 65% of the time.
        """

        categoryThreshold = 28
        # Obedience is a function of time
        obedienceThreshold = self.obedience_calculator(roundNumber)
        obey = self.roll_the_dice(obedienceThreshold)

        # If there's a lot of rocks...
        if pile > categoryThreshold and obey is True:
            move = self.win_conditions.get(Move.ROCK)

        # If there's a lot of paper...
        elif stack > categoryThreshold and obey is True:
            move = self.win_conditions.get(Move.PAPER)

        # If there's a lot of scissors...
        elif bin > categoryThreshold and obey is True:
            move = self.win_conditions.get(Move.SCISSORS)

        else:
            match roundNumber:
                case 1:
                    # I think Ben will play paper first round
                    move = Move.SCISSORS
                case 2:
                    # I think Ben will play paper second round
                    move = Move.SCISSORS
                case 3:
                    # I think Ben will play paper third round
                    move = Move.SCISSORS
                case 4:
                    # I think Ben is trying to get into my thought process so
                    # I'll think really hard about playing scissors so he goes
                    # rock and then play paper

                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    # move = Move.SCISSORS
                    move = Move.PAPER

                # Make Ben play against himself for a few rounds
                case 5:
                    move = self.ben_bot.make_move(history)
                case 6:
                    move = self.ben_bot.make_move(history)
                case 7:
                    move = self.ben_bot.make_move(history)
                case 8:
                    move = self.ben_bot.make_move(history)
                case 9:
                    move = self.ben_bot.make_move(history)
                case 10:
                    move = self.ben_bot.make_move(history)

                # Let's turn on the printer
                case 11:
                    move = Move.PAPER
                case 12:
                    move = Move.PAPER
                case 13:
                    move = Move.PAPER
                # Whoops some stuff fell in
                case 14:
                    move = Move.SCISSORS
                case 15:
                    move = Move.ROCK
                case 16:
                    move = Move.PAPER
                case 17:
                    move = Move.PAPER
                case 18:
                    move = Move.PAPER

                # Make Ben play against the Ben counter bot himself for a few more rounds
                case 19:
                    move = self.ben_counter(history)
                case 20:
                    move = self.ben_counter(history)
                case 21:
                    move = self.ben_counter(history)
                case 22:
                    move = self.ben_counter(history)
                case 23:
                    move = self.ben_counter(history)
                case 24:
                    move = self.ben_counter(history)
                case 25:
                    move = self.ben_counter(history)
                case 26:
                    move = self.ben_counter(history)
                case 27:
                    move = self.ben_counter(history)
                case 28:
                    move = self.ben_counter(history)
                case 29:
                    move = self.ben_counter(history)
                case 30:
                    move = self.ben_counter(history)
                    # soul read
                case 31:
                    move = Move.SCISSORS
                case 32:
                    move = Move.ROCK
                case 33:
                    move = Move.ROCK
                case 34:
                    move = Move.PAPER
                case 35:
                    move = Move.ROCK
                case 36:
                    move = Move.SCISSORS

                # If I can't think of anything just play a random move or counter ben
                case _:
                    if obey is True and (self.sin(roundNumber) > 0.5):
                        move = self.random_move()
                    elif self.sin(roundNumber < 0.25):
                        move = self.ben_counter(history)
                    else:
                        move = Move.ROCK

        self.ascii_art(move)
        return move

    def sin(self, x):
        return x - x**3/6 + x**5/120 - x**7/5040

    def obedience_calculator(self, roundNumber):
        obedienceLevel = .65 - roundNumber * .005 + 0.5 * self.sin(roundNumber / 101)
        obedienceThreshold = max(0, obedienceLevel)
        return obedienceThreshold

    def roll_the_dice(self, obedienceThreshold):
        obediencePercentage = random.randint(1, 100) / 100

        if obediencePercentage >= obedienceThreshold:
            return True
        else:
            return False

    def alter_history(self, history: list[RoundResult]) -> list[RoundResult]:
        while len(history) > 10:
            history.pop(0)

        return history

    def content_weigher(self, moveType, alternateHistory: list[RoundResult]) -> int:
        # The pile is weightless before we weight it
        weight = 0
        roundNumber = 0
        for round in alternateHistory:
            if round.opponent_move == moveType:
                weight += roundNumber
            roundNumber += 1

        return weight

    def get_weight(self, moveType, history: list[RoundResult]) -> int:
        alternateHistory = self.alter_history(history)
        return self.content_weigher(moveType, alternateHistory)

    def random_move(self):
        return random.choice([Move.ROCK, Move.PAPER, Move.SCISSORS])

    win_conditions = {
                        Move.SCISSORS: Move.ROCK,
                        Move.ROCK: Move.PAPER,
                        Move.PAPER: Move.SCISSORS
                    }

    def ben_counter(self, history: list[RoundResult]) -> Move:
        benMove = self.ben_bot.make_move(history)
        return self.win_conditions.get(benMove)

    rock_ascii = '''
        ⣠⡴⠖⠒⠲⠶⢤⣄⡀⠀⠀⠀⠀
⠀⠀⠀⢀⡾⠁⠀⣀⠔⠁⠀⠀⠈⠙⠷⣤⠦⣤⡀⠀
⣠⠞⠛⠛⠛⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠘⢧⠈⢿⡀
⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠟⠛⠛⠃⠸⡇⠈⣇
⣹⡷⠤⠤⠤⠄⠀⠀⠀⠀⢠⣤⡤⠶⠖⠛⠀⣿⠀⣿
⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡤⠖⠋⢀⣿⣠⠏
⢿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡾⠋⠁⠀
⠀⠉⢿⡋⠉⠉⠁⠀⠀⠀⠀⠀⢀⣠⠾⠋⠀⠀⠀⠀
⠀⠀⠈⠛⠶⠦⠤⠤⠤⠶⠶⠛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    '''

    paper_ascii = '''
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡴⠖⠒⢶⣄⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡼⠋⠀⠀⠀⢀⡿⠀⠀⠀⠀⠀⠀⠀
⢠⡶⠒⠳⠶⣄⠀⠀⠀⠀⠀⣴⠟⠁⠀⠀⠀⣰⠏⠀⢀⣤⣤⣄⡀⠀⠀
⠸⡇⠀⠀⠀⠘⣇⠀⠀⣠⡾⠁⠀⠀⠀⢀⣾⣣⡴⠚⠉⠀⠀⠈⠹⡆⠀
⠀⢻⡄⠀⠀⠀⢻⣠⡾⠋⠀⠀⠀⠀⣠⡾⠋⠁⠀⠀⠀⠀⢀⣠⡾⠃⠀
⠀⠀⣿⠀⠀⠀⠘⠉⠀⠀⠀⠀⠀⡰⠋⠀⠀⠀⠀⠀⣠⠶⠋⠁⠀⠀⠀
⠀⠠⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠁⠀⠀⠀⢀⣴⡿⠥⠶⠖⠛⠛⢶⡄
⢀⣰⡇⠀⠀⢀⡄⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⠀⠀⠀⠀⠀ ⢀⣠⠼⠃
⣿⠉⣇⠀⡴⠟⠁⣠⡾⠃⠀⠀⠀⠀⠀⠈⠀⠀⠀⣀⣤⠶⠛⠉⠀⠀⠀
⢻⡄⠹⣦⠀⠶⠛⢁⣠⡴⠀⠀⠀⠀⠀⠀⣠⡶⠛⠉⠀⠀⠀⠀⠀⠀⠀
⠀⠻⣄⠈⢷⣄⠈⠉⠁⠀⠀⠀⢀⣠⡴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠉⠳⢤⣭⡿⠒⠶⠶⠒⠚⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    '''

    scissors_ascii = '''
⠀⠀⠀⠀⢀⣠⣤⣀⣠⣤⠶⠶⠒⠶⠶⣤⣀⠀⠀⠀
⠀⠀⢀⡴⠋⣠⠞⠋⠁⠀⠀⠀⠀⠙⣄⠀⠙⢷⡀⠀
⠀⢀⡾⠁⣴⠋⠰⣤⣄⡀⠀⠀⠀⠀⠈⠳⢤⣼⣇⣀
⠀⢸⠃⢰⠇⠰⢦⣄⡈⠉⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠉⠛⠛⠓⠲⢦⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠸⣧⣿⠀⠻⣤⡈⠛⠳⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀  ⢻⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠈⠹⣆⠀⠈⠛⠂⠀⠀⠀⠀⠀⠀⠈⠐⠒⠒⠶⣶⣶⠶⠤⠤⣤⣠⡼⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠹⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠳⢦⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠈⠻⣦⣀⠀⠀⠀⠀⠐⠲⠤⣤⣀⡀⠀⠀⠀⠀⠀⠉⢳⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠉⠛⠶⠤⠤⠤⠶⠞⠋⠉⠙⠳⢦⣄⡀⠀⠀⠀⡷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀  ⠀⠀⠈⠙⠳⠦⠾⠃⠀⠀⠀
    '''

    def ascii_art(self, Move):
        match Move:
            case Move.ROCK:
                print(self.rock_ascii)
            case Move.PAPER:
                print(self.paper_ascii)
            case Move.SCISSORS:
                print(self.scissors_ascii)
            case _: 
                print('What the hell happened here?')

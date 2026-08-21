from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import List

class Move(Enum):
    ROCK     = "ROCK"
    PAPER    = "PAPER"
    SCISSORS = "SCISSORS"

@dataclass
class RoundResult:
    my_move      : Move
    opponent_move: Move
    result       : str # String name of your class


class RPSTemplate(ABC):
    """
    Inherit this template and implement the make_move function
    """
    
    @abstractmethod
    def make_move(self, history: List[RoundResult]) -> Move:
        pass
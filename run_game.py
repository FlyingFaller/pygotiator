import os
import importlib.util
import inspect
import concurrent.futures
from typing import Any
import itertools
from colorama import init, Fore, Style
import sys
import threading

from template import RPSTemplate, Move, RoundResult, Result

# Helper for indentation management
class ThreadSafeIndentingStdout:
    """Intercepts print statements and applies indentation."""
    def __init__(self):
        self.original_stdout = sys.stdout
        self.thread_locals = threading.local()
        self.lock = threading.Lock()

    def write(self, data):
        # Check if the current thread has an active prefix (indent)
        prefix = getattr(self.thread_locals, 'prefix', None)
        
        if prefix:
            with self.lock: # Prevent threads from printing over each other
                is_new_line = getattr(self.thread_locals, 'is_new_line', True)
                out = ""
                for char in data:
                    # Inject prefix at the start of a line
                    if is_new_line and char != '\n':
                        out += prefix
                        is_new_line = False
                    out += char
                    # Reset flag when we hit a newline
                    if char == '\n':
                        is_new_line = True
                        
                self.thread_locals.is_new_line = is_new_line
                self.original_stdout.write(out)
        else:
            # If no prefix is set (e.g., the main game engine), print normally
            self.original_stdout.write(data)

    def flush(self):
        self.original_stdout.flush()

# Init stuff
init()

sys.stdout = ThreadSafeIndentingStdout()

AVAILABLE_COLORS = [
    Fore.GREEN, Fore.BLUE, Fore.CYAN, Fore.MAGENTA, Fore.YELLOW,
    Fore.LIGHTGREEN_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTCYAN_EX,
    Fore.LIGHTMAGENTA_EX, Fore.LIGHTYELLOW_EX
]
_bot_colors_map = {}

# Main functions
def format_bot_name(bot_name: str, use_backticks: bool = True, pad_to: int = 0) -> str:
    """Assigns a persistent color to a bot name and returns the formatted ANSI string."""
    if bot_name not in _bot_colors_map:
        color = AVAILABLE_COLORS[len(_bot_colors_map) % len(AVAILABLE_COLORS)] # Cycle through each color
        _bot_colors_map[bot_name] = color
        
    text = f"`{bot_name}`" if use_backticks else bot_name

    # Pad here to avoid formatting issues with ANSI chars
    if pad_to > 0:
        text = f"{text:<{pad_to}}"
        
    return f"{_bot_colors_map[bot_name]}{text}{Style.RESET_ALL}" 

def load_bots(folder_path="bots", exclude=None) -> list[dict[str, Any]]:
    """
    Scans a folder for python files, loads them, and extracts any classes
    that inherit from RPSTemplate.
    """
    bots = []

    if exclude is None:
        exclude_list = []
    elif isinstance(exclude, str):
        exclude_list = [exclude]
    else:
        exclude_list = exclude
    
    for filename in os.listdir(folder_path):
        if filename in exclude_list:
            continue
        
        if filename.endswith(".py") and not filename.startswith("__"): 
            file_path = os.path.join(folder_path, filename)
            module_name = filename[:-3]
            
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for attribute_name, attribute_value in inspect.getmembers(module):
                if inspect.isclass(attribute_value):
                    if issubclass(attribute_value, RPSTemplate) and attribute_value is not RPSTemplate:
                        
                        bots.append({
                            "class_name"  : attribute_name,    # Bot name
                            "class_object": attribute_value,   # The uninitialized class blueprint
                            "file_source" : filename           # Bot source
                        })
                        
    return bots

def _determine_winner(move_a: Move, move_b: Move) -> bool:
    """Helper to evaluate match outcome."""
    win_conditions = {
        Move.ROCK: Move.SCISSORS,
        Move.PAPER: Move.ROCK,
        Move.SCISSORS: Move.PAPER
    }
    return win_conditions.get(move_a) == move_b

def _get_history(target_bot: str, opponent_bot: str, central_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Constructs the matchup history from the perspective of the target bot."""
    history = []
    for record in central_history:
        if record["bot_a"] == target_bot and record["bot_b"] == opponent_bot:
            history.append(RoundResult(
                my_move       = record["move_a"],
                opponent_move = record["move_b"],
                result        = record["result_a"]
            ))
        elif record["bot_a"] == opponent_bot and record["bot_b"] == target_bot:
            history.append(RoundResult(
                my_move       = record["move_b"],
                opponent_move = record["move_a"],
                result        = record["result_b"]
            ))
    return history

def run_tournament(bots: list[dict[str, Any]], num_rounds: int = 100, timeout_seconds: float = 20.0) -> list[dict[str, Any]]:
    """
    Runs a Round-Robin tournament between all loaded bots.
    """
    central_history = []
    err_style = f"{Fore.RED}{Style.BRIGHT}"
    
    for bot_a_info, bot_b_info in itertools.combinations(bots, 2):
        
        bot_a_name = bot_a_info["class_name"]
        bot_b_name = bot_b_info["class_name"]

        # Bot styles
        c_bot_a = format_bot_name(bot_a_name)
        c_bot_b = format_bot_name(bot_b_name)
        
        try:
            bot_a_instance = bot_a_info["class_object"]()
            bot_b_instance = bot_b_info["class_object"]()
        except Exception as e:
            # print(f"Failed to initialize match between {bot_a_name} and {bot_b_name}: {e}")
            print(f"{err_style}Failed to initialize match between {c_bot_a}{err_style} and {c_bot_b}{err_style}: {e}{Style.RESET_ALL}")
            continue

        for _ in range(num_rounds):
            hist_a = _get_history(bot_a_name, bot_b_name, central_history)
            hist_b = _get_history(bot_b_name, bot_a_name, central_history)
            
            # Make moves on different threads to enforce timeouts and 
            # prevent errors from taking down tourney
            move_a, move_b = None, None

            # Wrapper func to inject indents
            def run_bot(bot_func, history):
                sys.stdout.thread_locals.prefix = f"    " # Just an indent for now
                try:
                    return bot_func(history)
                finally:
                    # Clean up so the thread can be reused safely
                    sys.stdout.thread_locals.prefix = None
            
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
                
            # future_a = executor.submit(bot_a_instance.make_move, hist_a)
            # future_b = executor.submit(bot_b_instance.make_move, hist_b)

            future_a = executor.submit(run_bot, bot_a_instance.make_move, hist_a)
            future_b = executor.submit(run_bot, bot_b_instance.make_move, hist_b)
            
            # Bot A
            try:
                move_a = future_a.result(timeout=timeout_seconds)
                if not isinstance(move_a, Move): 
                    move_a = None
            except concurrent.futures.TimeoutError:
                move_a = None 
                # print(f'Bot `{bot_a_name}` timed out.')
                print(f"{err_style}Bot {c_bot_a}{err_style} timed out.{Style.RESET_ALL}")
            except Exception as e:
                move_a = None
                # print(f'Error in bot `{bot_a_name}`: {e}')
                print(f"{err_style}Error in bot {c_bot_a}{err_style}: {e}{Style.RESET_ALL}")

            # Bot B
            try:
                move_b = future_b.result(timeout=timeout_seconds)
                if not isinstance(move_b, Move): 
                    move_b = None
            except concurrent.futures.TimeoutError:
                move_b = None
                # print(f'Bot `{bot_b_name}` timed out.')
                print(f"{err_style}Bot {c_bot_b}{err_style} timed out.{Style.RESET_ALL}")
            except Exception as e:
                move_b = None
                # print(f'Error in bot `{bot_b_name}`: {e}')
                print(f"{err_style}Error in bot {c_bot_b}{err_style}: {e}{Style.RESET_ALL}")

            # Command shutdown so haning threads don't take out the entire tourney
            executor.shutdown(wait=False, cancel_futures=True)

            # Evaluate the results of the match
            result_a, result_b = Result.TIE, Result.TIE 
            
            if move_a is None and move_b is None:
                pass # Both forfeit
            elif move_a == move_b:
                pass # Standard Tie
            elif move_a is None:
                result_a, result_b = Result.LOSS, Result.WIN
            elif move_b is None:
                result_a, result_b = Result.WIN, Result.LOSS
            else:
                if _determine_winner(move_a, move_b):
                    result_a, result_b = Result.WIN, Result.LOSS
                else:
                    result_a, result_b = Result.LOSS, Result.WIN

            # Record match
            central_history.append({
                "bot_a"   : bot_a_name,
                "bot_b"   : bot_b_name,
                "move_a"  : move_a,
                "move_b"  : move_b,
                "result_a": result_a,
                "result_b": result_b
            })

            # Print match results
            # a_str = move_a.name if move_a else "FORFEIT"
            # b_str = move_b.name if move_b else "FORFEIT"

            a_str = move_a.name if move_a else f"{err_style}FORFEIT{Style.RESET_ALL}"
            b_str = move_b.name if move_b else f"{err_style}FORFEIT{Style.RESET_ALL}"

            # Determine the winner string
            if result_a == Result.WIN:
                # outcome = f"`{bot_a_name}` WINS"
                outcome = f"{c_bot_a} WINS"
            elif result_b == Result.WIN:
                # outcome = f"`{bot_b_name}` WINS"
                outcome = f"{c_bot_b} WINS"
            else:
                outcome = "TIE"
                
            # Concise output
            # print(f"`{bot_a_name}` ({a_str}) vs `{bot_b_name}` ({b_str}) -> {outcome}")
            print(f"{c_bot_a} ({a_str}) vs {c_bot_b} ({b_str}) -> {outcome}")
            
    return central_history

def calculate_scores(central_history: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """
    Parses the history output of run_tournament() to calculate final standings for each bot.
    Awards 1 point for a win, 0 for a tie, and 0 for a loss.
    """
    scoreboard = {}

    for match in central_history:
        bot_a = match["bot_a"]
        bot_b = match["bot_b"]

        # Initialize bots in scoreboard
        if bot_a not in scoreboard:
            scoreboard[bot_a] = {"wins": 0, "losses": 0, "ties": 0, "points": 0}
        if bot_b not in scoreboard:
            scoreboard[bot_b] = {"wins": 0, "losses": 0, "ties": 0, "points": 0}

        # Tally results for Bot A
        if match["result_a"] == Result.WIN:
            scoreboard[bot_a]["wins"] += 1
            scoreboard[bot_a]["points"] += 1
        elif match["result_a"] == Result.LOSS:
            scoreboard[bot_a]["losses"] += 1
        elif match["result_a"] == Result.TIE:
            scoreboard[bot_a]["ties"] += 1

        # Tally results for Bot B
        if match["result_b"] == Result.WIN:
            scoreboard[bot_b]["wins"] += 1
            scoreboard[bot_b]["points"] += 1
        elif match["result_b"] == Result.LOSS:
            scoreboard[bot_b]["losses"] += 1
        elif match["result_b"] == Result.TIE:
            scoreboard[bot_b]["ties"] += 1

    # Sort on decending points
    sorted_scoreboard = dict(
        sorted(scoreboard.items(), key=lambda item: item[1]["points"], reverse=True)
    )

    return sorted_scoreboard

if __name__ == "__main__":

    example_bots = ['all_rock_bot.py', 'ascii_bot.py', 'example_bot.py', 'tit4tat_bot.py', 'broken_bot.py']

    loaded_bots = load_bots(exclude=['broken_bot.py', 'all_rock_bot.py', 'example_bot.py', 'tit4tat_bot.py']) # Change to exclude=example_bots for real tournament!
    history = run_tournament(loaded_bots, num_rounds=20, timeout_seconds=20.0)
    final_scores = calculate_scores(history)
    
    print("\n--- TOURNAMENT RESULTS ---")
    for rank, (bot_name, stats) in enumerate(final_scores.items(), start=1):
        # print(f"{rank}. {bot_name:<15}: {stats['points']} pts ({stats['wins']}W - {stats['losses']}L - {stats['ties']}T)")
        c_bot_name = format_bot_name(bot_name, use_backticks=False, pad_to=15)
        print(f"{rank}. {c_bot_name}: {stats['points']} pts ({stats['wins']}W - {stats['losses']}L - {stats['ties']}T)")
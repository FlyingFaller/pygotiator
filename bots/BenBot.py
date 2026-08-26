from template import Move, RoundResult, RPSTemplate
from enum import Enum
import logging
import random
from pystac_client import Client
from datetime import datetime, timedelta, timezone
import time
import matplotlib.pyplot as plt
import numpy as np
import hashlib
import fsspec 
import tifffile
import requests
from io import BytesIO
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Set higher during runtime to keep console clean

class BenBot(RPSTemplate):
    class FeatureSet(Enum):
        RANDOM         = "random_select"
        LAVALAMP       = "lava_lamp"
        TAROT          = "tarot_reading"
        CLOUDS         = "cloud_analysis"
        WEIGHTEDRANDOM = "weighted_random"
        WIKI           = "wikipedia_select"

    ACTIVE_FEATURES = {
        FeatureSet.RANDOM        : True,
        FeatureSet.LAVALAMP      : False,
        FeatureSet.TAROT         : True,
        FeatureSet.CLOUDS        : True,
        FeatureSet.WEIGHTEDRANDOM: False,
        FeatureSet.WIKI          : False
    }

    DEBUG = False

    def __init__(self):
        pass

    def make_move(self, history: list[RoundResult]) -> Move:
        start_time = time.time()

        # Filter active features
        active_features = [
            feature for feature, active in self.ACTIVE_FEATURES.items() if active
        ]

        if not active_features: 
            logger.warning("No features active,  defaulting to `random_select`.")
            return self.random_select()

        # Randomly select a feature for this round
        selected_feature = random.choice(active_features)
        method_func = getattr(self, selected_feature.value, "random_select") # Default to random

        logger.info(f"Selected {selected_feature.name}!")

        # Run and return selected method
        try:
            return method_func(history)
        except Exception as e:
            logger.error(f"Failed to run selected `{selected_feature.name}` with error: {e}. Defaulting to random.") 
            return self.random_select(history)
        finally:
            runtime = time.time() - start_time
            if runtime > 20: logger.error(f"Runtime exceeded: {runtime:.3f} sec.")
            elif runtime > 15: logger.warning(f"Runtime close to exceeding limits: {runtime:.3f} sec.")
            else: logger.info(f"Runtime: {runtime:.3f} sec.")

    def random_select(self, history: list[RoundResult]):
        """Basic random selection"""
        return random.choice([Move.ROCK, Move.PAPER, Move.SCISSORS])

    def lava_lamp(self, history: list[RoundResult]):
        pass

    def tarot_reading(self, history: list[RoundResult]):
        tarot_map = {
              # --- Major Arcana (22) ---
            "The Fool"          : Move.PAPER,    "The Magician"  : Move.SCISSORS,
            "The High Priestess": Move.ROCK,     "The Empress"   : Move.ROCK,
            "The Emperor"       : Move.ROCK,     "The Hierophant": Move.ROCK,
            "The Lovers"        : Move.PAPER,    "The Chariot"   : Move.ROCK,
            "Strength"          : Move.ROCK,     "The Hermit"    : Move.PAPER,
            "Wheel of Fortune"  : Move.SCISSORS, "Justice"       : Move.SCISSORS,
            "The Hanged Man"    : Move.SCISSORS, "Death"         : None,
            "Temperance"        : Move.PAPER,    "The Devil"     : Move.ROCK,
            "The Tower"         : None,          "The Star"      : Move.PAPER,
            "The Moon"          : Move.ROCK,     "The Sun"       : Move.SCISSORS,
            "Judgement"         : Move.ROCK,     "The World"     : Move.SCISSORS,
            
              # --- Suit of Wands (14) ---
            "Ace of Wands"  : Move.ROCK,     "Two of Wands"   : Move.ROCK,
            "Three of Wands": Move.ROCK,     "Four of Wands"  : Move.PAPER,
            "Five of Wands" : Move.ROCK,     "Six of Wands"   : Move.SCISSORS,
            "Seven of Wands": Move.SCISSORS, "Eight of Wands" : Move.PAPER,
            "Nine of Wands" : Move.ROCK,     "Ten of Wands"   : Move.SCISSORS,
            "Page of Wands" : Move.ROCK,     "Knight of Wands": Move.ROCK,
            "Queen of Wands": Move.ROCK,     "King of Wands"  : Move.ROCK,

              # --- Suit of Cups (14) ---
            "Ace of Cups"  : Move.PAPER,    "Two of Cups"   : Move.PAPER,
            "Three of Cups": Move.SCISSORS, "Four of Cups"  : Move.ROCK,
            "Five of Cups" : Move.ROCK,     "Six of Cups"   : Move.PAPER,
            "Seven of Cups": Move.SCISSORS, "Eight of Cups" : Move.SCISSORS,
            "Nine of Cups" : Move.ROCK,     "Ten of Cups"   : Move.PAPER,
            "Page of Cups" : Move.ROCK,     "Knight of Cups": Move.SCISSORS,
            "Queen of Cups": Move.PAPER,    "King of Cups"  : Move.SCISSORS,

              # --- Suit of Swords (14) ---
            "Ace of Swords"  : Move.SCISSORS, "Two of Swords"   : Move.ROCK,
            "Three of Swords": Move.SCISSORS, "Four of Swords"  : Move.SCISSORS,
            "Five of Swords" : Move.SCISSORS, "Six of Swords"   : Move.SCISSORS,
            "Seven of Swords": Move.SCISSORS, "Eight of Swords" : Move.SCISSORS,
            "Nine of Swords" : Move.SCISSORS, "Ten of Swords"   : None,
            "Page of Swords" : Move.SCISSORS, "Knight of Swords": Move.ROCK,
            "Queen of Swords": Move.SCISSORS, "King of Swords"  : Move.SCISSORS,

              # --- Suit of Pentacles (14) ---
            "Ace of Pentacles"  : Move.PAPER, "Two of Pentacles"   : Move.PAPER,
            "Three of Pentacles": Move.PAPER, "Four of Pentacles"  : Move.PAPER,
            "Five of Pentacles" : Move.ROCK,  "Six of Pentacles"   : Move.PAPER,
            "Seven of Pentacles": Move.PAPER, "Eight of Pentacles" : Move.PAPER,
            "Nine of Pentacles" : Move.PAPER, "Ten of Pentacles"   : Move.PAPER,
            "Page of Pentacles" : Move.PAPER, "Knight of Pentacles": Move.PAPER,
            "Queen of Pentacles": Move.PAPER, "King of Pentacles"  : Move.PAPER
        }

        with open("bots/tarot_ansi_deck.json", "r", encoding="utf-8") as f:
            deck_art = json.load(f)

        selected_card = random.choice(list(tarot_map.keys()))

        print(deck_art[selected_card])
        print(f'{selected_card.upper():^60}\n')
        return tarot_map[selected_card]


    def cloud_analysis(self, history: list[RoundResult]):
        api_url = "https://earth-search.aws.element84.com/v1"
        client = Client.open(api_url)

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=8)

        search = client.search(
            collections=["sentinel-2-l2a"],
            datetime=[start_time, end_time],
            max_items=100, # Adjust until under runtime limits
            query={
                "s2:nodata_pixel_percentage": {"lt": 20}, # Ensures a full-ish frame
                "eo:cloud_cover": {"gt": 10, "lt": 90}    # Ensures between 10% and 90% cloud cover
            }
        )

        if not search.matched():
            raise ValueError("No satellite images found for datetime range.")

        items = list(search.items())
        selection = random.choice(items).assets # Dict of assets

        scl_url = selection['scl'].href # Scene Classification Layer
        thumbnail_url = selection['thumbnail'].href

        # Stream the remote COG via HTTP range requests using fsspec, f rasterio!
        scl_url = selection['scl'].href
        with fsspec.open(scl_url, mode='rb') as f:
            with tifffile.TiffFile(f) as tif:
                level_idx = min(3, len(tif.series[0].levels) - 1) # There are levels to this shit (0 for highest res)
                scl_data = tif.series[0].levels[level_idx].asarray()

        cloud_mask = np.isin(scl_data, [8, 9, 10]) # Clouds are classified as 8-10
        cloud_bytes = cloud_mask.tobytes()
        cloud_idx = int(hashlib.sha256(cloud_bytes).hexdigest(), 16) % 3

        if self.DEBUG:
            response = requests.get(thumbnail_url)
            response.raise_for_status()
            thumbnail_img = plt.imread(BytesIO(response.content), format='jpg')

            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

            ax1.imshow(thumbnail_img)
            ax1.set_title("True Color Thumbnail")
            ax1.axis('off')

            ax2.imshow(scl_data, cmap='tab20')
            ax2.set_title("SCL Layer")
            ax2.axis('off')

            ax3.imshow(cloud_mask, cmap='gray')
            ax3.set_title("Cloud Mask")
            ax3.axis('off')

            plt.tight_layout()
            plt.show(block=False) 
            plt.pause(3)
            plt.close()

        return [Move.ROCK, Move.PAPER, Move.SCISSORS][cloud_idx]

    def weighted_random(self, history: list[RoundResult]):
        pass

    def wikipedia_select(self, history: list[RoundResult]):
        pass


if __name__ == "__main__":
    bot = BenBot()
    output = bot.make_move(history=[])
    print(f'Output: {output}')
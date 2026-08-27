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
import wikipediaapi
from transformers import pipeline
from collections import Counter, deque
import cv2

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Set higher during runtime to keep console clean

class BenBot(RPSTemplate):
    class FeatureSet(Enum):
        RANDOM   = "random_select"
        LAVALAMP = "lava_lamp"
        TAROT    = "tarot_reading"
        CLOUDS   = "cloud_analysis"
        STANLEY  = "stanley_select"
        WIKI     = "wikipedia_select"

    # (is_active, weight)
    ACTIVE_FEATURES = {
        FeatureSet.RANDOM  : (True,  1.0),
        FeatureSet.LAVALAMP: (True,   1.0),
        FeatureSet.TAROT   : (True,  1.0),
        FeatureSet.CLOUDS  : (True,  1.0),
        FeatureSet.STANLEY : (True,  1.0),
        FeatureSet.WIKI    : (True,  1.0)
    }

    DEBUG = False

    NROUNDS = 20

    CAMERA_INDEX = 0
    CAMERA_WIDTH = 540
    CAMERA_HEIGHT = 960

    LAVALAMP_THINK_TIME = 1 # seconds

    cap = None # Global camera capture

    def __init__(self):
        if self.ACTIVE_FEATURES[self.FeatureSet.WIKI][0]:
            logger.info('Loading classifier model...')
            self.classifier = pipeline(
                "zero-shot-classification", 
                model="typeform/distilbert-base-uncased-mnli" # Some model or some shit idk bro
            )

        if self.ACTIVE_FEATURES[self.FeatureSet.LAVALAMP][0]:
            if BenBot.cap is None or not BenBot.cap.isOpened():
                BenBot.cap = cv2.VideoCapture(self.CAMERA_INDEX, cv2.CAP_DSHOW)
                BenBot.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.CAMERA_WIDTH)
                BenBot.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.CAMERA_HEIGHT)

            self.frame_buffer = deque(maxlen=90)

    def make_move(self, history: list[RoundResult]) -> Move:
        """Orchestrator to call on the different move methods."""
        start_time = time.time()

        # Filter active features
        active_features = []
        weights = []
        for feature, (is_active, weight) in self.ACTIVE_FEATURES.items():
            if is_active:
                active_features.append(feature)
                weights.append(weight)

        if not active_features: 
            logger.warning("No features active, defaulting to `random_select`.")
            return self.random_select()

        # Randomly select a feature for this round
        selected_feature = random.choices(active_features, weights=weights, k=1)[0]
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

    def random_select(self, history: list[RoundResult]) -> Move:
        """Basic random selection"""
        return random.choice([Move.ROCK, Move.PAPER, Move.SCISSORS])

    def lava_lamp(self, history: list[RoundResult]) -> Move:
        """
        Uses lava lamp noise to generate random moves. 

        Setup steps:    
        1. Visit VDO.Ninja on the iPhone, select Add OBS Camera, configure and start
        2. Open OBS Studio and add browser source, configure resolution, framerate, and source URL to those provided by VDO.Ninja
        3. Start Vitual Camera in OBS Studio
        4. Check CV2 settings at top of this script
        """
        self.frame_buffer.clear()
        start_time = time.time()

        while True:
            ret, frame = BenBot.cap.read()

            if not ret:
                raise Exception('Recieved no images!')

            
            blurred_frame = cv2.GaussianBlur(frame, (21, 21), 0)
            self.frame_buffer.append(blurred_frame)

            if len(self.frame_buffer) == self.frame_buffer.maxlen:
                oldest_frame = self.frame_buffer[0]
                newest_frame = blurred_frame

                delta = cv2.absdiff(oldest_frame, newest_frame)
                gray_delta = cv2.cvtColor(delta, cv2.COLOR_BGR2GRAY)
                _, thresh_delta = cv2.threshold(gray_delta, 25, 255, cv2.THRESH_BINARY)

                if self.DEBUG:
                    cv2.imshow('Motion Map', thresh_delta)  

                if time.time() - start_time > self.LAVALAMP_THINK_TIME:
                    frame_bytes = thresh_delta.tobytes()
                    hash_hex = hashlib.sha256(frame_bytes).hexdigest()
                    hash_int = int(hash_hex, 16)
                    return [Move.ROCK, Move.PAPER, Move.SCISSORS][hash_int % 3]

            if self.DEBUG:
                cv2.imshow('Live View', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            

    def tarot_reading(self, history: list[RoundResult]) -> Move|None:
        """Pull a random tarot card in the terminal and choose a move based on vibes."""
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

    def cloud_analysis(self, history: list[RoundResult]) -> Move:
        """Uses recent Sentinel 2 l2a Scene Classification Layer data to choose a move."""
        api_url = "https://earth-search.aws.element84.com/v1"
        client = Client.open(api_url)

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=8)

        search = client.search(
            collections=["sentinel-2-l2a"],
            datetime=[start_time, end_time],
            max_items=min(100, self.NROUNDS), # Adjust until under runtime limits
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

    def stanley_select(self, history: list[RoundResult]) -> Move:
        """A weighted random move selection from our old pal Stanley."""
        if len(history) < self.NROUNDS/5:
            return self.random_select(history)

        opponent_moves = [result.opponent_move for result in history]
        counts = Counter(opponent_moves)
        
        weights = [
            counts.get(Move.SCISSORS, 0), 
            counts.get(Move.ROCK, 0), 
            counts.get(Move.PAPER, 0)
        ]

        return random.choices([Move.ROCK, Move.PAPER, Move.SCISSORS], weights=weights)[0]

    def wikipedia_select(self, history: list[RoundResult]) -> Move:
        """Move selection based on random english Wikipedia article text."""
        wiki = wikipediaapi.Wikipedia(
            user_agent='PyGotiator (bengsaunders@gmail.com)', 
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI # Return raw text not HTML
            )
        pages = wiki.random(limit=1)
        if pages: 
            page = list(pages.values())[0]
        else:
            raise ValueError('Failed to fetch a page.')

        logger.info(f"Found article: `{page.title}`.")

        func = random.choice([
            self._text_len_2_move, 
            self._text_hash_2_move, 
            self._text_semantic_2_move
            ])

        return func(page.text)     

    def _text_len_2_move(self, text: str) -> Move:
        """Move from text length."""
        logger.info('Using text length.')
        text_len = len(text.split())
        move = [Move.ROCK, Move.PAPER, Move.SCISSORS][text_len%3]
        logger.info(f'The article contains {text_len} word(s). Choosing {move.name}!')
        return move

    def _text_hash_2_move(self, text: str) -> Move:
        """Move from text hash."""
        logger.info('Using text hash.')
        hash_hex = hashlib.sha256(text.encode('utf-8')).hexdigest()
        hash_int = int(hash_hex, 16)
        return [Move.ROCK, Move.PAPER, Move.SCISSORS][hash_int%3]

    def _text_semantic_2_move(self, text: str) -> Move:
        """Move from semantic similarity of text."""
        labels = {'rock': Move.ROCK, 'paper': Move.PAPER, 'scissors': Move.SCISSORS}
        logger.info('Using semantic analysis.')
        result = self.classifier(text, list(labels.keys()))
        logger.info(f'The article was most sematically similar to the concept of `{result['labels'][0].upper()}` with a score of {result['scores'][0]:.2%}')
        return labels[result['labels'][0]]

if __name__ == "__main__":
    bot = BenBot()
    for _ in range(5):
        output = bot.make_move(history=[])
        print(f'Output: {output}')
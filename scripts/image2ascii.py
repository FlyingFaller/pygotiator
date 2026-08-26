import os
import json
import climage

TAROT_DECK_NAMES = [
    # --- Major Arcana (22) ---
    "The Fool", "The Magician", "The High Priestess", "The Empress", 
    "The Emperor", "The Hierophant", "The Lovers", "The Chariot", 
    "Strength", "The Hermit", "Wheel of Fortune", "Justice", 
    "The Hanged Man", "Death", "Temperance", "The Devil", 
    "The Tower", "The Star", "The Moon", "The Sun", 
    "Judgement", "The World",
    
    # --- Suit of Wands (14) ---
    "Ace of Wands", "Two of Wands", "Three of Wands", "Four of Wands", "Five of Wands",
    "Six of Wands", "Seven of Wands", "Eight of Wands", "Nine of Wands", "Ten of Wands",
    "Page of Wands", "Knight of Wands", "Queen of Wands", "King of Wands",

    # --- Suit of Cups (14) ---
    "Ace of Cups", "Two of Cups", "Three of Cups", "Four of Cups", "Five of Cups",
    "Six of Cups", "Seven of Cups", "Eight of Cups", "Nine of Cups", "Ten of Cups",
    "Page of Cups", "Knight of Cups", "Queen of Cups", "King of Cups",

    # --- Suit of Swords (14) ---
    "Ace of Swords", "Two of Swords", "Three of Swords", "Four of Swords", "Five of Swords",
    "Six of Swords", "Seven of Swords", "Eight of Swords", "Nine of Swords", "Ten of Swords",
    "Page of Swords", "Knight of Swords", "Queen of Swords", "King of Swords",

    # --- Suit of Pentacles (14) ---
    "Ace of Pentacles", "Two of Pentacles", "Three of Pentacles", "Four of Pentacles", "Five of Pentacles",
    "Six of Pentacles", "Seven of Pentacles", "Eight of Pentacles", "Nine of Pentacles", "Ten of Pentacles",
    "Page of Pentacles", "Knight of Pentacles", "Queen of Pentacles", "King of Pentacles"
]

INPUT_DIR = "scripts/tarot_cards_color"
OUTPUT_FILE = "bots/tarot_ansi_deck.json"

def build_deck():
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Directory {INPUT_DIR} not found.")
        return

    # Sort alphanumerically
    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    files.sort() 

    deck_data = {}
    print(f"Found {len(files)} images. Starting conversion...")

    for index, filename in enumerate(files):
        if index >= len(TAROT_DECK_NAMES):
            print(f"Warning: More files than cards. Skipping {filename}.")
            continue
            
        card_name = TAROT_DECK_NAMES[index]
        file_path = os.path.join(INPUT_DIR, filename)
        
        print(f"Converting [{card_name}] from {filename}...")
        
        try:
            # Magic conversion
            ansi_output = climage.convert(
                file_path, 
                is_unicode=True,
                width=60
            )
            
            # Store the mapped output
            deck_data[card_name] = ansi_output
        except Exception as e:
            print(f"Error converting {filename}: {e}.")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deck_data, f, indent=4)
        

if __name__ == "__main__":
    build_deck()
    with open("bots/tarot_ansi_deck.json", "r", encoding="utf-8") as f:
        deck_art = json.load(f)

    print(deck_art["Death"])
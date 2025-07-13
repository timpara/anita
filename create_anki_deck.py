import csv
import openai
import os

from anita.deck_generator import AnkiDeckGenerator


if __name__ == "__main__":
    # --- Configuration ---
    INPUT_CSV = os.path.join('resources','restaurant.csv')
    OUTPUT_DECK_FILE = "Italian_Vocabulary_Deck.apkg"

    # --- Choose your TTS provider ---

    # -- Option 1: Use OpenAI for TTS (Default) --
    # generator = AnkiDeckGenerator(tts_provider="openai")

    # -- Option 2: Use ElevenLabs for TTS --
    # Make sure you have set the ELEVENLABS_API_KEY environment variable.
    # You can find voice IDs on the ElevenLabs website. "Bella" is a popular choice.
    generator = AnkiDeckGenerator(
        tts_provider="elevenlabs",
        deck_name="Italian Vocabulary with ElevenLabs TTS",
    )

    # --- Run the generator ---
    try:
        generator.generate_deck(INPUT_CSV, OUTPUT_DECK_FILE)
    except Exception as e:
        print(f"\n--- FATAL ERROR ---")
        print(f"The program stopped because of an error: {e}")
        print("Please check the setup instructions at the top of the script.")



import csv
import openai
import os

from anita.deck_generator import AnkiDeckGenerator

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")

# --- Example Usage ---
if __name__ == "__main__":
    # Create a dummy input.csv for demonstration
    with open('input.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['hello', 'ciao'])
        writer.writerow(['cat', 'gatto'])
        writer.writerow(['dog', 'cane'])
        writer.writerow(['house', 'casa'])

    deck_generator = AnkiDeckGenerator(deck_name="Italian Vocabulary Restaurant",
                                        deck_id=1234567890,
                                        output_media_dir="media"  # This will create a 'media' folder
)
    deck_generator.run(input_csv_path=os.path.join('resources','restaurant.csv'),
                       output_anki_filename='italian_vocab_with_images.apkg')



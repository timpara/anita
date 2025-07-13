import csv
import os

import genanki
import openai
import requests
from PIL import Image

class AnkiDeckGenerator:
    def __init__(self, deck_name="Italian Vocabulary Deck with Images", deck_id=1234567891, output_media_dir="media"):
        self.deck_name = deck_name
        self.deck_id = deck_id
        self.output_media_dir = output_media_dir
        self.deck = genanki.Deck(self.deck_id, self.deck_name)
        self.package = genanki.Package(self.deck)
        self.model = self._create_anki_model()

        os.makedirs(self.output_media_dir, exist_ok=True)

    def _create_anki_model(self):
        """Creates and returns the Anki model for the deck."""
        return genanki.Model(
            1607392319,
            'Model with Audio and Small Image',
            fields=[
                {'name': 'English'},
                {'name': 'Italian'},
                {'name': 'Audio'},
                {'name': 'Image'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '{{English}}',
                    'afmt': '''
                        {{FrontSide}}
                        <hr id="answer">
                        {{Italian}}<br>
                        {{Audio}}<br><br>
                        <div style="max-width: 128px; margin: auto;">
                            {{Image}}
                        </div>
                    ''',
                },
            ],
            css='''
                .card {
                    font-family: arial;
                    font-size: 20px;
                    text-align: center;
                    color: black;
                    background-color: white;
                }
                img {
                    max-width: 128px;
                    height: auto;
                }
            '''
        )

    def _generate_tts(self, text, output_filename):
        """Generates text-to-speech audio."""
        try:
            response = openai.audio.speech.create(
                model='tts-1',
                voice='alloy',
                input=text
            )
            response.stream_to_file(output_filename)
            return True
        except Exception as e:
            print(f"TTS Error for '{text}': {e}")
            return False

    def _generate_image(self, prompt, output_filename):
        """Generates an image using DALL-E."""
        try:
            response = openai.images.generate(
                model="dall-e-2",
                prompt=f"{prompt}, simple illustration, clean, minimal, white background",
                n=1,
                size="256x256"
            )
            image_url = response.data[0].url

            img_data = requests.get(image_url).content
            with open(output_filename, 'wb') as handler:
                handler.write(img_data)
            return True
        except Exception as e:
            print(f"Image generation error for '{prompt}': {e}")
            return False

    def _optimize_image_size(self, image_path, target_size=(128, 128)):
        """Optimizes image size using Pillow."""
        try:
            with Image.open(image_path) as img:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                img.save(image_path, 'PNG', optimize=True)
        except ImportError:
            print("Pillow not installed, skipping image optimization.")
        except Exception as e:
            print(f"Error optimizing image '{image_path}': {e}")

    def generate_deck(self, input_csv_path, output_anki_filename):
        """
        Main method to generate the Anki deck.

        Args:
            input_csv_path (str): Path to the CSV file containing vocabulary.
                                  Each row should have (English, Italian).
            output_anki_filename (str): Name of the output Anki package file (.apkg).
        """
        try:
            with open(input_csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for idx, row in enumerate(reader):
                    if len(row) < 2:
                        print(f"Skipping row {idx + 1} due to insufficient columns: {row}")
                        continue

                    english, italian = row[0], row[1]
                    print(f"Processing card {idx + 1}: {english} - {italian}")

                    audio_fname = f'italian_audio_{idx}.mp3'
                    image_fname = f'image_{idx}.png'

                    audio_path = os.path.join(self.output_media_dir, audio_fname)
                    image_path = os.path.join(self.output_media_dir, image_fname)

                    # Generate TTS
                    if self._generate_tts(italian, audio_path):
                        print(f"  ✓ Generated audio for '{italian}'")
                    else:
                        print(f"  ✗ Failed to generate audio for '{italian}'")
                        audio_path = None # Don't add to media files if generation failed

                    # Generate Image
                    if self._generate_image(english, image_path):
                        print(f"  ✓ Generated image for '{english}'")
                        self._optimize_image_size(image_path)
                    else:
                        print(f"  ✗ Failed to generate image for '{english}'")
                        image_path = None # Don't add to media files if generation failed

                    # Create Anki note
                    image_html = f'<img src="{image_fname}">' if image_path else ''
                    audio_field = f'[sound:{audio_fname}]' if audio_path else ''

                    note = genanki.Note(
                        model=self.model,
                        fields=[english, italian, audio_field, image_html]
                    )
                    self.deck.add_note(note)

                    # Add media files to package
                    if audio_path:
                        self.package.media_files.append(audio_path)
                    if image_path:
                        self.package.media_files.append(image_path)

            self.package.write_to_file(output_anki_filename)
            print(f"\n✅ Anki Deck Created: {output_anki_filename}")

        except FileNotFoundError:
            print(f"Error: Input CSV file not found at '{input_csv_path}'")
        except Exception as e:
            print(f"An unexpected error occurred during deck generation: {e}")

    def run(self, input_csv_path, output_anki_filename):
        """Runner method to parametrize and execute deck generation."""
        self.generate_deck(input_csv_path, output_anki_filename)

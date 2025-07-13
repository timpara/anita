import csv
import os

import genanki
import openai
import requests
from PIL import Image

# We import elevenlabs only if it's going to be used.
try:
    import elevenlabs
    from elevenlabs import Voice, VoiceSettings
    from elevenlabs.client import ElevenLabs  # This is correct
except ImportError:
    elevenlabs = None


class AnkiDeckGenerator:
    """
    Generates an Anki deck from a CSV file, with optional images from DALL-E and
    audio from a selected Text-to-Speech (TTS) provider (OpenAI or ElevenLabs).
    """

    def __init__(self,
                 deck_name="Italian Vocabulary Deck with Images",
                 deck_id=1234567891,
                 output_media_dir="media",
                 tts_provider="openai",
                 elevenlabs_voice_id="CiwzbDpaN3pQXjTgx3ML",
                 generate_images=False):  # New parameter
        """
        Initializes the AnkiDeckGenerator.

        Args:
            deck_name (str): The name of the Anki deck to be created.
            deck_id (int): A unique ID for the Anki deck.
            output_media_dir (str): Directory to store temporary media files.
            tts_provider (str): The TTS service to use. 'openai' or 'elevenlabs'.
            elevenlabs_voice_id (str): The voice ID to use for ElevenLabs TTS.
            generate_images (bool): Whether to generate images using OpenAI. Defaults to False.
        """
        self.deck_name = deck_name
        self.deck_id = deck_id
        self.output_media_dir = output_media_dir
        self.tts_provider = tts_provider.lower()
        self.elevenlabs_voice_id = elevenlabs_voice_id
        self.generate_images = generate_images  # Store the parameter

        self.elevenlabs_client = None

        self.deck = genanki.Deck(self.deck_id, self.deck_name)
        self.package = genanki.Package(self.deck)
        self.model = self._create_anki_model()

        os.makedirs(self.output_media_dir, exist_ok=True)
        self._initialize_apis()

    def _initialize_apis(self):
        """Checks for and sets up the required API keys."""
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        openai.api_key = os.getenv("OPENAI_API_KEY")

        if self.tts_provider == 'elevenlabs':
            if elevenlabs is None:
                raise ImportError("The 'elevenlabs' package is not installed. Please run 'pip install elevenlabs'.")

            elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
            if not elevenlabs_api_key:
                raise ValueError("ELEVENLABS_API_KEY environment variable not set. It is required for ElevenLabs TTS.")

            self.elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)

        elif self.tts_provider != 'openai':
            raise ValueError(f"Unsupported TTS provider: '{self.tts_provider}'. Choose 'openai' or 'elevenlabs'.")

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
        if self.tts_provider == 'elevenlabs':
            return self._generate_tts_elevenlabs(text, output_filename)
        return self._generate_tts_openai(text, output_filename)

    def _generate_tts_openai(self, text, output_filename):
        try:
            response = openai.audio.speech.create(
                model='tts-1',
                voice='alloy',
                input=text
            )
            response.stream_to_file(output_filename)
            return True
        except Exception as e:
            print(f"OpenAI TTS Error for '{text}': {e}")
            return False

    def _generate_tts_elevenlabs(self, text, output_filename):
        if self.elevenlabs_client is None:
            print("ElevenLabs client not initialized.")
            return False
        try:
            audio = self.elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=self.elevenlabs_voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            with open(output_filename, 'wb') as f:
                for chunk in audio:
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"ElevenLabs TTS Error for '{text}': {e}")
            return False

    def _generate_image(self, prompt, output_filename):
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
        try:
            with Image.open(image_path) as img:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                img.save(image_path, 'PNG', optimize=True)
        except Exception as e:
            print(f"Error optimizing image '{image_path}': {e}")

    def generate_deck(self, input_csv_path, output_anki_filename):
        try:
            with open(input_csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for idx, row in enumerate(reader):
                    if len(row) < 2:
                        print(f"Skipping row {idx + 1} due to insufficient columns: {row}")
                        continue

                    english, italian = row[0].strip(), row[1].strip()
                    print(f"Processing card {idx + 1}: {english} - {italian}")

                    safe_eng_word = "".join(c for c in english if c.isalnum())
                    audio_fname = f'audio_{safe_eng_word}_{idx}.mp3'
                    image_fname = f'image_{safe_eng_word}_{idx}.png'

                    audio_path = os.path.join(self.output_media_dir, audio_fname)
                    image_path = os.path.join(self.output_media_dir, image_fname)

                    if self._generate_tts(italian, audio_path):
                        print(f"  ✓ Generated audio for '{italian}' via {self.tts_provider.capitalize()}")
                    else:
                        print(f"  ✗ Failed to generate audio for '{italian}'")
                        audio_path = None

                    if self.generate_images:
                        if self._generate_image(english, image_path):
                            print(f"  ✓ Generated image for '{english}'")
                            self._optimize_image_size(image_path)
                        else:
                            print(f"  ✗ Failed to generate image for '{english}'")
                            image_path = None
                    else:
                        image_path = None

                    image_html = f'<img src="{image_fname}">' if image_path else ''
                    audio_field = f'[sound:{audio_fname}]' if audio_path else ''

                    note = genanki.Note(
                        model=self.model,
                        fields=[english, italian, audio_field, image_html]
                    )
                    self.deck.add_note(note)

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
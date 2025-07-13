# Anita - Anki Deck Generator

A Python tool that automatically generates Anki flashcard decks with audio pronunciation and images. Perfect for language learners who want to create multimedia vocabulary decks.

## Features

- **Automated flashcard creation** from CSV vocabulary lists
- **Text-to-Speech audio** generation for pronunciation using OpenAI's TTS API
- **AI-generated images** for visual learning using DALL-E 2
- **Optimized media files** with automatic image resizing
- **Clean, minimalist card design** focused on effective learning

## Prerequisites

- Python 3.7+
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/anita.git
cd anita
```

2. Install required dependencies:
```bash
pip install genanki openai requests pillow
```

3. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

### Basic Usage

```python
from anita.deck_generator import AnkiDeckGenerator

# Create generator instance
generator = AnkiDeckGenerator(
    deck_name="Italian Vocabulary Deck",
    deck_id=1234567891
)

# Generate deck from CSV file
generator.run("vocabulary.csv", "italian_deck.apkg")
```

### CSV Format

Your input CSV file should have two columns: English and target language (e.g., Italian).

Example `vocabulary.csv`:
```
apple,mela
house,casa
book,libro
water,acqua
```

### Command Line Usage

```bash
python -m anita.deck_generator vocabulary.csv output_deck.apkg
```

## Configuration

The `AnkiDeckGenerator` class accepts the following parameters:

- `deck_name`: Name of your Anki deck (default: "Italian Vocabulary Deck with Images")
- `deck_id`: Unique identifier for the deck (default: 1234567891)
- `output_media_dir`: Directory for storing generated media files (default: "media")

## Generated Card Format

Each flashcard includes:
- **Front**: English word
- **Back**: 
  - Target language translation
  - Audio pronunciation
  - AI-generated illustration (128x128px)

## API Usage

The tool uses OpenAI APIs for:
- **TTS-1** model for audio generation
- **DALL-E 2** for image generation

Note: API usage will incur costs based on OpenAI's pricing.

## Error Handling

The generator includes robust error handling:
- Skips rows with insufficient data
- Continues processing if individual media generation fails
- Provides detailed console output for tracking progress

## Example Output

```
Processing card 1: apple - mela
  ✓ Generated audio for 'mela'
  ✓ Generated image for 'apple'
Processing card 2: house - casa
  ✓ Generated audio for 'casa'
  ✓ Generated image for 'house'

✅ Anki Deck Created: italian_deck.apkg
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [genanki](https://github.com/kerrickstaley/genanki) for Anki deck generation
- [OpenAI](https://openai.com/) for TTS and image generation APIs



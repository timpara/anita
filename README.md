# Anita - Smart Anki Deck Generator

![Anita Banner](https://via.placeholder.com/800x200.png?text=Anita+-+AI-Powered+Anki+Deck+Generator)

Automatically create rich multimedia Anki decks with AI-generated audio pronunciations and illustrations. Perfect for language learners seeking immersive vocabulary practice.

## ✨ Features

- 📄 Convert CSV word lists into Anki decks in minutes
- 🔊 Generate native-like pronunciation audio using OpenAI TTS (or ElevenLabs*)
- 🖼️ Create memorable illustrations with DALL-E 2 (optional)
- 🖌️ Automatic image optimization (resized to 128x128px)
- 📦 Clean, distraction-free card design
- 🛠️ Robust error handling and progress tracking

_* ElevenLabs integration optional_

## 📋 Prerequisites

- Python 3.10+
- OpenAI API Key (optional)
- ElevenLabs API Key (optional, recoommended for premium TTS)

## 🚀 Installation

1. **Clone repository**
   ```bash
   git clone https://github.com/yourusername/anita.git
   cd anita
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Set API keys**
   ```bash
   # Required OpenAI key
   export OPENAI_API_KEY='your-openai-key-here'
   
   # Optional ElevenLabs key
   export ELEVENLABS_API_KEY='your-elevenlabs-key-here'
   ```

## 🛠️ Usage

### Command Line Interface
```bash
python -m anita.deck_generator vocabulary.csv output_deck.apkg
```

### Python API
```python
from anita.deck_generator import AnkiDeckGenerator

generator = AnkiDeckGenerator(
    deck_name="Italian Essentials",
    deck_id=1234567891
)

generator.run("vocabulary.csv", "my_deck.apkg")
```

### CSV Format Requirements
Create a CSV with `English,Translation` pairs:

```csv
apple,mela
house,casa
book,libro
water,acqua
```

## 🔧 Configuration

Customize the generator with these parameters:

| Parameter           | Default                      | Description                  |
|---------------------|------------------------------|------------------------------|
| `deck_name`         | "Italian Vocabulary Deck"    | Name shown in Anki           |
| `deck_id`           | 1234567891                   | Unique deck identifier       |
| `output_media_dir`  | "media"                      | Media storage directory      |
| `image_size`        | (128, 128)                   | Image dimensions in pixels   |

## 🎴 Card Preview

**Front Side**  
`apple`

**Back Side**  
- **Translation**: mela  
- **Pronunciation**: 🔊 Audio playback  
- **Visual Aid**: 🖼️ AI-generated apple image

## 🤖 API Integration

| Service     | Use Case             | Model       | Cost Implications         |
|-------------|----------------------|-------------|---------------------------|
| OpenAI      | Text-to-Speech       | TTS-1       | $0.015 per 1k characters  |
| OpenAI      | Image Generation     | DALL-E 2    | $0.020 per image          |
| ElevenLabs  | Premium TTS (Optional)| v1         | Depends on subscription   |

## 📝 Example Workflow

```text
Processing card 1: apple - mela
  ✓ Generated audio (OpenAI) for 'mela'
  ✓ Generated image for 'apple' (128x128px)
Processing card 2: house - casa
  ✓ Generated audio (OpenAI) for 'casa'
  ✓ Generated image for 'house' (128x128px)

✅ Deck created: italian_deck.apkg (4 cards)
```

## ⚠️ Important Notes

- API costs are incurred for each generation
- Maintain CSV formatting for error-free processing
- Store media files locally to avoid regeneration costs
- First run may take longer due to media generation

## 🤝 Contributing

We welcome contributions! Please see our [Contribution Guidelines](CONTRIBUTING.md) for details.

## 📄 License

MIT License - See [LICENSE](LICENSE) for full text.

## 🙏 Acknowledgments

- [genanki](https://github.com/kerrickstaley/genanki) for Anki deck creation
- OpenAI for cutting-edge AI models
- ElevenLabs for premium voice synthesis options

---

_🔄 Refresh your language learning with AI-powered spaced repetition!_
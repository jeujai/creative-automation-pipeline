# Creative Automation Pipeline

A command-line tool that automates the generation of social media advertising creative assets using GenAI. The system processes campaign briefs, manages existing assets, generates new images when needed, and produces outputs in multiple aspect ratios with text overlays.

## Features

- **Campaign Brief Processing**: Parse JSON/YAML campaign briefs with multiple products
- **Smart Asset Management**: Reuse existing product assets to minimize generation costs
- **GenAI Image Generation**: Generate new hero images via OpenAI DALL-E 3 when assets are missing
- **Multi-Format Output**: Create variants in 1:1, 9:16, and 16:9 aspect ratios for different social platforms
- **Text Overlay**: Apply campaign messages with proper contrast and readability
- **Organized Output**: Systematic organization by campaign, product, and aspect ratio
- **Optional Compliance**: Brand compliance and legal content checking
- **Comprehensive Logging**: Detailed execution reporting and logging

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key (for DALL-E 3 image generation)

### Setup

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API key:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_api_key_here
```

Alternatively, export the API key directly:
```bash
export OPENAI_API_KEY=your_api_key_here
```

## Usage

### Basic Usage

Run the pipeline with a campaign brief:

```bash
python pipeline.py --brief examples/example_brief.yaml
```

### Command-Line Options

```bash
python pipeline.py --brief <brief_file> [options]

Required:
  --brief PATH          Path to campaign brief file (JSON or YAML)

Optional:
  --config PATH         Path to custom configuration file (default: config.yaml)
  --compliance          Enable brand and legal compliance checks
  --verbose            Enable verbose debug logging
  --help               Show help message
```

### Examples

```bash
# Basic execution with YAML brief (Superman in Japan campaign)
python pipeline.py --brief examples/example_brief.yaml

# Use JSON brief format
python pipeline.py --brief examples/example_brief.json

# Enable compliance checks
python pipeline.py --brief examples/example_brief.yaml --compliance

# Use custom configuration
python pipeline.py --brief examples/example_brief.yaml --config custom_config.yaml

# Verbose logging for debugging
python pipeline.py --brief examples/example_brief.yaml --verbose
```

**Example Output:**
The Superman in Japan campaign will generate 6 creative assets:
- `output/superman_japan_2024/superman_tokyo_tower/1x1_superman_tokyo_tower.png` (Instagram feed)
- `output/superman_japan_2024/superman_tokyo_tower/9x16_superman_tokyo_tower.png` (Stories/TikTok)
- `output/superman_japan_2024/superman_tokyo_tower/16x9_superman_tokyo_tower.png` (YouTube)
- `output/superman_japan_2024/superman_shibuya/1x1_superman_shibuya.png`
- `output/superman_japan_2024/superman_shibuya/9x16_superman_shibuya.png`
- `output/superman_japan_2024/superman_shibuya/16x9_superman_shibuya.png`

Each image will have the Japanese text "ヒーローが日本に来る！" (The Hero Comes to Japan!) overlaid at the bottom.

## Campaign Brief Format

Campaign briefs can be provided in JSON or YAML format. The system automatically detects the format based on file extension.

### Required Fields

- `campaign_id`: Unique identifier for the campaign
- `products`: List of products (each with `product_id` and `name`)
- `target_region`: Geographic target market
- `target_audience`: Description of target audience
- `campaign_message`: Text to overlay on generated assets

### Optional Fields

- `localization`: Language and region-specific messaging

### Example YAML Brief

```yaml
campaign_id: "summer_sale_2024"
products:
  - product_id: "coffee_premium"
    name: "Premium Arabica Coffee"
  - product_id: "tea_organic"
    name: "Organic Green Tea"
target_region: "US"
target_audience: "health-conscious millennials"
campaign_message: "Start your day right"
```

### Example JSON Brief

```json
{
  "campaign_id": "summer_sale_2024",
  "products": [
    {
      "product_id": "coffee_premium",
      "name": "Premium Arabica Coffee"
    },
    {
      "product_id": "tea_organic",
      "name": "Organic Green Tea"
    }
  ],
  "target_region": "US",
  "target_audience": "health-conscious millennials",
  "campaign_message": "Start your day right"
}
```

## Configuration

The pipeline uses `config.yaml` for configuration. Key settings include:

### GenAI Configuration

```yaml
genai:
  provider: "openai"
  model: "dall-e-3"
  default_size: [1024, 1024]
```

### Storage Configuration

```yaml
storage:
  input_dir: "./input_assets"
  output_dir: "./output"
```

### Aspect Ratios

```yaml
aspect_ratios:
  - "1:1"    # Square (Instagram posts, Facebook)
  - "9:16"   # Vertical (Instagram Stories, TikTok)
  - "16:9"   # Horizontal (YouTube, Facebook video)
```

### Text Overlay

```yaml
text_overlay:
  font_family: "Arial"
  font_size: 48
  color: "#FFFFFF"
  position: "bottom"
  padding: 20
  background_opacity: 0.6
```

### Compliance (Optional)

```yaml
compliance:
  enabled: false
  brand:
    logo_template: "./brand/logo.png"
    brand_colors: ["#FF0000", "#0000FF"]
  legal:
    prohibited_words: ["guarantee", "free", "winner"]
```

### Logging

```yaml
logging:
  level: "INFO"
  file: "./pipeline.log"
```

## Input Assets

Place existing product images in the `input_assets/` directory. The filename should match the `product_id` from your campaign brief.

### Naming Convention

```
input_assets/
  ├── {product_id}.png
  ├── {product_id}.jpg
  └── {product_id}.jpeg
```

### Example

For a product with `product_id: "coffee_premium"`, place the image as:
- `input_assets/coffee_premium.png` or
- `input_assets/coffee_premium.jpg`

If an input asset exists, the pipeline will reuse it. If not, it will generate a new image using GenAI.

## Output Structure

Generated assets are organized systematically:

```
output/
└── {campaign_id}/
    └── {product_id}/
        ├── 1x1_{product_id}.png
        ├── 9x16_{product_id}.png
        └── 16x9_{product_id}.png
```

### Example Output

```
output/
└── summer_sale_2024/
    ├── coffee_premium/
    │   ├── 1x1_coffee_premium.png
    │   ├── 9x16_coffee_premium.png
    │   └── 16x9_coffee_premium.png
    └── tea_organic/
        ├── 1x1_tea_organic.png
        ├── 9x16_tea_organic.png
        └── 16x9_tea_organic.png
```

Each output includes:
- The campaign message overlaid on the image
- Proper aspect ratio for the target platform
- High-quality image preservation

## Key Design Decisions

### Modular Architecture

The pipeline uses a modular component-based architecture:
- **BriefParser**: Handles JSON/YAML parsing
- **AssetManager**: Manages file storage and retrieval
- **GenAIClient**: Interfaces with OpenAI DALL-E 3
- **ImageCompositor**: Creates aspect ratio variants and text overlays
- **ComplianceChecker**: Optional brand and legal validation
- **PipelineOrchestrator**: Coordinates all components

This design allows easy extension (e.g., adding new GenAI providers or storage backends).

### Asset Reuse Strategy

The pipeline checks for existing input assets before generating new ones. This:
- Reduces API costs
- Maintains consistency across campaigns
- Speeds up execution for products with existing assets

### Smart Cropping

Different aspect ratios use intelligent cropping strategies:
- **1:1 (Square)**: Center crop to maintain focal point
- **9:16 (Vertical)**: Top-focused crop for Stories format
- **16:9 (Horizontal)**: Center crop for landscape orientation

### Text Overlay with Contrast

Text overlays include:
- Semi-transparent background for readability
- Automatic font scaling based on image dimensions
- Configurable positioning and styling
- Multi-line text wrapping support

### Error Handling

The pipeline implements graceful error handling:
- Validates briefs early and fails fast on invalid input
- Retries GenAI API calls with exponential backoff (max 3 attempts)
- Continues processing other products if one fails
- Provides detailed error logging for debugging

## Assumptions and Limitations

### Assumptions

1. **API Access**: Assumes valid OpenAI API key with DALL-E 3 access
2. **Local Execution**: Designed for local development environment
3. **Image Formats**: Supports PNG, JPG, and JPEG formats
4. **English Text**: Text overlay optimized for English language
5. **File System**: Assumes write permissions to output directory
6. **Network**: Requires internet connection for GenAI API calls

### Limitations

1. **GenAI Provider**: Currently only supports OpenAI DALL-E 3 (Stability AI fallback not implemented)
2. **Language Support**: Text overlay only supports English (no multi-language font handling)
3. **Video**: Does not support video asset generation
4. **Cloud Storage**: No direct integration with cloud storage (Azure, AWS, Dropbox)
5. **Batch Processing**: Processes one campaign at a time
6. **Real-time**: Not designed for real-time or high-throughput scenarios
7. **Image Quality**: GenAI output quality depends on API provider capabilities
8. **Cost**: Each GenAI generation incurs API costs (DALL-E 3: ~$0.04-0.08 per image)
9. **Compliance**: Compliance checking is basic (template matching, keyword scanning)
10. **Font Availability**: Requires system fonts to be available for text overlay

### Performance Expectations

- **Asset Reuse**: < 1 second per variant
- **GenAI Generation**: 10-30 seconds per image (API dependent)
- **Image Composition**: < 2 seconds per variant
- **Total Pipeline**: ~30-60 seconds for 2 products × 3 aspect ratios with generation

## Troubleshooting

### Common Issues

**"OpenAI API key not found"**
- Ensure `OPENAI_API_KEY` is set in environment or `.env` file
- Verify the key is valid and has DALL-E 3 access

**"Campaign brief not found"**
- Check the file path provided to `--brief`
- Ensure the file exists and has `.json` or `.yaml` extension

**"Failed to generate image"**
- Check your OpenAI API quota and billing status
- Verify internet connection
- Review `pipeline.log` for detailed error messages

**"Permission denied" when saving outputs**
- Ensure write permissions for the output directory
- Check available disk space

**"Font not found" for text overlay**
- Install required system fonts
- Update `font_family` in `config.yaml` to an available font

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src

# Run specific test file
pytest tests/test_brief_parser.py

# Verbose output
pytest tests/ -v
```

## Project Structure

```
.
├── pipeline.py                 # Main CLI entry point
├── config.yaml                 # Configuration file
├── requirements.txt            # Python dependencies
├── .env.example               # API key template
├── README.md                  # This file
│
├── src/                       # Source code
│   ├── models.py              # Data models
│   ├── orchestrator.py        # Main orchestrator
│   ├── parsers/               # Brief parsing
│   ├── managers/              # Asset management
│   ├── clients/               # GenAI clients
│   ├── compositors/           # Image composition
│   ├── compliance/            # Compliance checking
│   └── utils/                 # Logging and reporting
│
├── tests/                     # Test suite
├── input_assets/              # Input product images
├── output/                    # Generated outputs
├── examples/                  # Example briefs
└── brand/                     # Brand assets
```

## License

This is a proof-of-concept project for demonstration purposes.

## Support

For issues or questions, please review the troubleshooting section or check the execution logs in `pipeline.log`.

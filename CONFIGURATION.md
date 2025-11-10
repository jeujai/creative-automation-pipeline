# Configuration Guide

This document provides detailed information about configuring the Creative Automation Pipeline.

## Configuration Files

The pipeline uses two configuration mechanisms:

1. **config.yaml** - Main configuration file for pipeline settings
2. **.env** - Environment variables for sensitive data (API keys)

## Environment Variables

### Setup

1. Copy the example file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```bash
# Required
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Optional
STABILITY_API_KEY=your-stability-api-key-here
PIPELINE_CONFIG=./config.yaml
LOG_LEVEL=INFO
```

### Available Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for DALL-E 3 | None |
| `STABILITY_API_KEY` | No | Stability AI API key (fallback) | None |
| `PIPELINE_CONFIG` | No | Path to custom config.yaml | `./config.yaml` |
| `LOG_LEVEL` | No | Override logging level | From config.yaml |

### Getting API Keys

**OpenAI API Key:**
1. Sign up at https://platform.openai.com/
2. Navigate to API Keys section
3. Create a new API key
4. Ensure you have credits/billing set up
5. DALL-E 3 access is required

**Stability AI API Key (Optional):**
1. Sign up at https://platform.stability.ai/
2. Navigate to API Keys
3. Create a new API key

## Configuration File (config.yaml)

### GenAI Settings

Controls image generation behavior:

```yaml
genai:
  provider: "openai"              # GenAI provider to use
  api_key: "${OPENAI_API_KEY}"    # API key (loaded from environment)
  model: "dall-e-3"               # Model to use
  default_size: [1024, 1024]      # Default image size [width, height]
  max_retries: 3                  # Max retry attempts on API failure
  retry_delay: 2                  # Initial retry delay (exponential backoff)
```

**Options:**
- `provider`: Currently supports `"openai"` (Stability AI not yet implemented)
- `model`: For OpenAI, use `"dall-e-3"` or `"dall-e-2"`
- `default_size`: DALL-E 3 supports `[1024, 1024]`, `[1024, 1792]`, `[1792, 1024]`
- `max_retries`: Recommended 3-5 for production
- `retry_delay`: Seconds to wait before first retry (doubles each retry)

### Storage Settings

Controls where files are read from and written to:

```yaml
storage:
  input_dir: "./input_assets"           # Existing product images
  output_dir: "./output"                # Generated outputs
  supported_formats: ["png", "jpg", "jpeg"]  # Supported formats
```

**Options:**
- `input_dir`: Relative or absolute path to input assets
- `output_dir`: Relative or absolute path for outputs
- `supported_formats`: List of image extensions to recognize

**Output Structure:**
```
output/
└── {campaign_id}/
    └── {product_id}/
        ├── 1x1_{product_id}.png
        ├── 9x16_{product_id}.png
        └── 16x9_{product_id}.png
```

### Aspect Ratio Settings

Defines which aspect ratios to generate:

```yaml
aspect_ratios:
  - "1:1"    # Square
  - "9:16"   # Vertical
  - "16:9"   # Horizontal
```

**Common Aspect Ratios:**
- `1:1` - Instagram feed, Facebook posts
- `9:16` - Instagram Stories, TikTok, Snapchat
- `16:9` - YouTube, Facebook video, LinkedIn
- `4:5` - Instagram portrait (not currently supported)

**Cropping Strategy:**
- `1:1`: Center crop to maintain focal point
- `9:16`: Top-focused crop for vertical format
- `16:9`: Center crop for landscape

### Text Overlay Settings

Controls how campaign messages are displayed:

```yaml
text_overlay:
  font_family: "Arial"          # Font name
  font_size: 48                 # Base font size in pixels
  color: "#FFFFFF"              # Text color (hex)
  position: "bottom"            # Vertical position
  padding: 20                   # Padding in pixels
  background_opacity: 0.6       # Background transparency (0.0-1.0)
  max_width_ratio: 0.9          # Max text width (0.0-1.0)
  line_spacing: 1.2             # Line spacing multiplier
```

**Options:**
- `font_family`: Any system font name (e.g., "Arial", "Helvetica", "Times New Roman")
- `font_size`: Base size - automatically scaled based on image dimensions
- `color`: Hex color code (e.g., "#FFFFFF" for white, "#000000" for black)
- `position`: `"top"`, `"center"`, or `"bottom"`
- `padding`: Space around text in pixels
- `background_opacity`: 0.0 (transparent) to 1.0 (opaque)
- `max_width_ratio`: Percentage of image width for text (0.0-1.0)
- `line_spacing`: Multiplier for line height (1.0 = single spacing)

**Font Availability:**
- Ensure the specified font is installed on your system
- On macOS: Check Font Book
- On Linux: Check `/usr/share/fonts/`
- On Windows: Check `C:\Windows\Fonts\`

### Compliance Settings (Optional)

Enable brand and legal compliance checking:

```yaml
compliance:
  enabled: false  # Set to true to enable
  
  brand:
    logo_template: "./brand/logo.png"
    brand_colors:
      - "#FF0000"
      - "#0000FF"
    min_logo_size: [50, 50]
    color_tolerance: 30
  
  legal:
    prohibited_words:
      - "guarantee"
      - "free"
      - "winner"
    case_sensitive: false
```

**Brand Compliance:**
- `logo_template`: Path to brand logo image for template matching
- `brand_colors`: List of approved brand colors (hex format)
- `min_logo_size`: Minimum logo dimensions [width, height] in pixels
- `color_tolerance`: Color matching tolerance (0-255, lower = stricter)

**Legal Compliance:**
- `prohibited_words`: List of terms to flag in campaign messages
- `case_sensitive`: Whether matching is case-sensitive

**Usage:**
```bash
# Enable compliance checks
python pipeline.py --brief campaign.yaml --compliance
```

### Logging Settings

Controls logging behavior:

```yaml
logging:
  level: "INFO"                 # Log level
  file: "./pipeline.log"        # Log file path
  console_output: true          # Print to console
  include_timestamp: true       # Include timestamps
```

**Log Levels:**
- `DEBUG`: Detailed information for debugging
- `INFO`: General informational messages (recommended)
- `WARNING`: Warning messages for recoverable issues
- `ERROR`: Error messages for failures

**Usage:**
```bash
# Override log level via command line
python pipeline.py --brief campaign.yaml --verbose  # Sets DEBUG level
```

### Performance Settings

Future optimization settings:

```yaml
performance:
  parallel_processing: false    # Enable parallel processing (future)
  max_workers: 4                # Max concurrent workers
  cache_enabled: false          # Enable response caching (future)
```

**Note:** These settings are placeholders for future enhancements and are not currently implemented.

## Configuration Examples

### Minimal Configuration

For basic usage with defaults:

```yaml
genai:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"
  model: "dall-e-3"

storage:
  input_dir: "./input_assets"
  output_dir: "./output"

aspect_ratios:
  - "1:1"
  - "9:16"
  - "16:9"

text_overlay:
  font_family: "Arial"
  font_size: 48
  color: "#FFFFFF"
  position: "bottom"

logging:
  level: "INFO"
  file: "./pipeline.log"
```

### Production Configuration

For production use with compliance:

```yaml
genai:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"
  model: "dall-e-3"
  default_size: [1024, 1024]
  max_retries: 5
  retry_delay: 3

storage:
  input_dir: "/data/input_assets"
  output_dir: "/data/output"

aspect_ratios:
  - "1:1"
  - "9:16"
  - "16:9"

text_overlay:
  font_family: "Helvetica"
  font_size: 52
  color: "#FFFFFF"
  position: "bottom"
  padding: 30
  background_opacity: 0.7

compliance:
  enabled: true
  brand:
    logo_template: "/data/brand/logo.png"
    brand_colors: ["#FF6B35", "#004E89"]
    min_logo_size: [75, 75]
    color_tolerance: 20
  legal:
    prohibited_words: ["guarantee", "free", "winner", "risk-free", "miracle"]
    case_sensitive: false

logging:
  level: "INFO"
  file: "/var/log/pipeline.log"
  console_output: true
```

### Development Configuration

For development and testing:

```yaml
genai:
  provider: "openai"
  api_key: "${OPENAI_API_KEY}"
  model: "dall-e-3"
  max_retries: 2
  retry_delay: 1

storage:
  input_dir: "./test_assets"
  output_dir: "./test_output"

aspect_ratios:
  - "1:1"  # Test with just one aspect ratio

text_overlay:
  font_family: "Arial"
  font_size: 36
  color: "#FFFF00"  # Yellow for visibility
  position: "center"

compliance:
  enabled: false

logging:
  level: "DEBUG"
  file: "./debug.log"
  console_output: true
```

## Using Custom Configuration

### Via Command Line

```bash
# Use custom config file
python pipeline.py --brief campaign.yaml --config custom_config.yaml
```

### Via Environment Variable

```bash
# Set in .env file
PIPELINE_CONFIG=./custom_config.yaml

# Or export directly
export PIPELINE_CONFIG=./custom_config.yaml
python pipeline.py --brief campaign.yaml
```

## Configuration Validation

The pipeline validates configuration on startup:

**Required Settings:**
- GenAI provider and API key
- Storage directories (must be writable)
- At least one aspect ratio

**Optional Settings:**
- Compliance settings (only validated if enabled)
- Font settings (validated when text overlay is applied)

**Validation Errors:**

```
ERROR: OpenAI API key not found
→ Set OPENAI_API_KEY in .env file

ERROR: Output directory not writable
→ Check permissions on output directory

ERROR: Font 'CustomFont' not found
→ Install font or change font_family in config
```

## Best Practices

### Security

1. **Never commit .env files** - Add to `.gitignore`
2. **Use environment variables** for API keys
3. **Rotate API keys** regularly
4. **Limit API key permissions** to minimum required

### Performance

1. **Reuse input assets** when possible to save API costs
2. **Use appropriate image sizes** - larger isn't always better
3. **Enable caching** for development (when implemented)
4. **Monitor API usage** and set up billing alerts

### Reliability

1. **Set appropriate retry limits** (3-5 recommended)
2. **Use exponential backoff** for retries
3. **Monitor log files** for errors and warnings
4. **Test configuration** before production use

### Cost Optimization

1. **Reuse existing assets** - saves ~$0.04-0.08 per image
2. **Generate at optimal size** - DALL-E 3 charges per generation, not size
3. **Batch campaigns** when possible
4. **Monitor API costs** via OpenAI dashboard

## Troubleshooting

### Configuration Not Loading

```bash
# Check config file syntax
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Verify environment variables
echo $OPENAI_API_KEY
```

### Font Not Found

```bash
# List available fonts (macOS)
fc-list | grep -i arial

# Install fonts (Ubuntu)
sudo apt-get install fonts-liberation
```

### API Key Issues

```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Permission Errors

```bash
# Check directory permissions
ls -la output/

# Fix permissions
chmod 755 output/
```

## Advanced Configuration

### Multiple Environments

Create environment-specific configs:

```bash
config.dev.yaml
config.staging.yaml
config.prod.yaml
```

Use with:
```bash
python pipeline.py --brief campaign.yaml --config config.prod.yaml
```

### Configuration Inheritance

Create a base config and override specific settings:

```yaml
# base_config.yaml
genai:
  provider: "openai"
  model: "dall-e-3"

# Override in custom_config.yaml
genai:
  provider: "openai"
  model: "dall-e-3"
  max_retries: 10  # Override just this setting
```

## Support

For configuration issues:
1. Check this documentation
2. Review `pipeline.log` for errors
3. Validate YAML syntax
4. Verify environment variables are set
5. Test with minimal configuration first

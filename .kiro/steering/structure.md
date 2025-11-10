# Project Structure

## Directory Organization

```
.
├── pipeline.py                 # Main CLI entry point
├── config.yaml                 # Configuration file
├── requirements.txt            # Python dependencies
├── .env.example               # API key template
├── README.md                  # Documentation
│
├── src/                       # Source code modules
│   ├── __init__.py
│   ├── models.py              # Data models (CampaignBrief, Product, etc.)
│   ├── orchestrator.py        # PipelineOrchestrator
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── brief_parser.py    # BriefParser for JSON/YAML
│   ├── managers/
│   │   ├── __init__.py
│   │   └── asset_manager.py   # AssetManager for storage
│   ├── clients/
│   │   ├── __init__.py
│   │   ├── genai_client.py    # GenAIClient base class
│   │   └── openai_client.py   # OpenAI DALL-E implementation
│   ├── compositors/
│   │   ├── __init__.py
│   │   └── image_compositor.py # ImageCompositor for variants
│   ├── compliance/
│   │   ├── __init__.py
│   │   └── checker.py         # ComplianceChecker (optional)
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # PipelineLogger
│       └── reporter.py        # Report generation
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── test_brief_parser.py
│   ├── test_asset_manager.py
│   ├── test_image_compositor.py
│   └── fixtures/              # Test data
│
├── input_assets/              # Input product images
│   ├── product_a.png
│   └── product_b.jpg
│
├── output/                    # Generated outputs
│   └── {campaign_id}/
│       └── {product_id}/
│           ├── 1x1_{product_id}.png
│           ├── 9x16_{product_id}.png
│           └── 16x9_{product_id}.png
│
├── examples/                  # Example briefs
│   ├── example_brief.json
│   └── example_brief.yaml
│
└── brand/                     # Brand assets (optional)
    └── logo.png
```

## File Naming Conventions

- **Python modules**: lowercase with underscores (brief_parser.py)
- **Classes**: PascalCase (BriefParser, AssetManager)
- **Functions/methods**: lowercase with underscores (parse_brief, get_asset)
- **Output files**: {aspect_ratio}_{product_id}.{ext} (1x1_product_a.png)
- **Campaign briefs**: descriptive names with .json or .yaml extension

## Input/Output Conventions

### Campaign Brief Format

Briefs can be JSON or YAML with this structure:
- campaign_id: Unique identifier
- products: List of products with product_id and name
- target_region: Geographic target
- target_audience: Audience description
- campaign_message: Text to overlay on assets
- localization: Optional language/region-specific content

### Asset Organization

- Input assets stored in `input_assets/` with filename matching product_id
- Outputs organized by campaign_id, then product_id, then aspect ratio
- Preserve original image quality in outputs
- Support PNG, JPG, JPEG formats

## Code Organization Principles

- One class per file for major components
- Group related functionality in subdirectories (parsers, managers, clients)
- Keep orchestrator thin - delegate to specialized components
- Separate data models from business logic
- Utils for cross-cutting concerns (logging, reporting)

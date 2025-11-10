# Technology Stack

## Language & Runtime

- Python 3.9+

## Core Dependencies

- **Pillow (PIL)**: Image processing, resizing, cropping, text overlay
- **PyYAML**: YAML configuration and brief parsing
- **OpenAI SDK**: DALL-E 3 API integration for image generation
- **argparse**: Command-line interface

## Optional Dependencies

- **Stability SDK**: Fallback GenAI provider (Stability AI)
- **requests**: HTTP operations for image downloads

## Architecture Patterns

- **Modular component design**: Separate concerns into distinct classes (BriefParser, AssetManager, GenAIClient, ImageCompositor, ComplianceChecker, PipelineOrchestrator)
- **Dataclass models**: Use Python dataclasses for structured data (CampaignBrief, Product, PipelineResult, GeneratedAsset)
- **Strategy pattern**: Pluggable GenAI providers and storage backends
- **Orchestrator pattern**: Central PipelineOrchestrator coordinates all components

## Configuration Management

- YAML-based configuration file (config.yaml)
- Environment variables for sensitive data (API keys)
- Command-line argument overrides

## Common Commands

```bash
# Install dependencies
pip install pillow pyyaml openai requests

# Run pipeline with campaign brief
python pipeline.py --brief campaign_brief.yaml

# Run with custom config
python pipeline.py --brief campaign_brief.yaml --config custom_config.yaml

# Enable compliance checks
python pipeline.py --brief campaign_brief.yaml --compliance

# Verbose logging
python pipeline.py --brief campaign_brief.yaml --verbose

# Run tests
pytest tests/
```

## Error Handling Strategy

- Validate inputs early and fail fast
- Graceful degradation for missing assets (fallback to GenAI generation)
- Retry logic with exponential backoff for API failures (max 3 attempts)
- Continue processing other products if one fails
- Clear logging at INFO, WARNING, ERROR, DEBUG levels

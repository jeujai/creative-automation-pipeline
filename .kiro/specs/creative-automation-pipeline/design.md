# Design Document: Creative Automation Pipeline

## Overview

The Creative Automation Pipeline is a command-line application that automates the generation of social media advertising creative assets. The system processes campaign briefs, manages existing assets, generates new images using GenAI when needed, applies text overlays, and produces outputs in multiple aspect ratios.

### Technology Stack

- **Language**: Python 3.9+
- **GenAI Image Generation**: OpenAI DALL-E 3 API (primary) with fallback to Stability AI
- **Image Processing**: Pillow (PIL) for resizing, cropping, and text overlay
- **Configuration**: YAML and JSON parsing via PyYAML and built-in json modules
- **Storage**: Local filesystem with optional cloud storage abstraction layer
- **CLI Framework**: argparse for command-line interface

### Design Principles

1. **Modularity**: Separate concerns into distinct components (brief parsing, asset management, generation, composition)
2. **Extensibility**: Design for easy addition of new GenAI providers, storage backends, and compliance checks
3. **Fail-safe**: Graceful degradation when assets or services are unavailable
4. **Transparency**: Clear logging and reporting of all operations

## Architecture

### High-Level Architecture

```
┌─────────────────┐
│  Campaign Brief │
│   (JSON/YAML)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         Pipeline Orchestrator           │
│  - Parse brief                          │
│  - Coordinate components                │
│  - Generate outputs                     │
└───┬─────────┬─────────┬─────────┬──────┘
    │         │         │         │
    ▼         ▼         ▼         ▼
┌────────┐ ┌──────┐ ┌──────┐ ┌─────────┐
│ Asset  │ │GenAI │ │Image │ │Compliance│
│Manager │ │Client│ │Comp. │ │Checker  │
└────────┘ └──────┘ └──────┘ └─────────┘
    │         │         │         │
    └─────────┴─────────┴─────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Output Storage │
         └────────────────┘
```

### Component Interaction Flow

1. **Input Phase**: Pipeline Orchestrator reads and validates campaign brief
2. **Asset Resolution**: Asset Manager checks for existing assets, requests generation if needed
3. **Generation Phase**: GenAI Client generates missing hero images
4. **Composition Phase**: Image Compositor creates variants (aspect ratios + text overlay)
5. **Validation Phase**: Compliance Checker validates outputs (optional)
6. **Output Phase**: Organized assets saved to output directory with report

## Components and Interfaces

### 1. Pipeline Orchestrator

**Responsibility**: Main entry point that coordinates the entire pipeline execution

**Interface**:
```python
class PipelineOrchestrator:
    def __init__(self, config: PipelineConfig):
        """Initialize with configuration"""
        
    def run(self, brief_path: str) -> PipelineResult:
        """Execute pipeline for given campaign brief"""
        
    def _validate_brief(self, brief: CampaignBrief) -> bool:
        """Validate brief structure and required fields"""
```

**Key Methods**:
- `run()`: Main execution method
- `_validate_brief()`: Ensures brief has required fields
- `_process_product()`: Processes single product through pipeline
- `_generate_report()`: Creates execution summary

### 2. Campaign Brief Parser

**Responsibility**: Parse and validate campaign brief files

**Interface**:
```python
class BriefParser:
    @staticmethod
    def parse(file_path: str) -> CampaignBrief:
        """Parse JSON or YAML brief file"""
        
    @staticmethod
    def _detect_format(file_path: str) -> str:
        """Detect file format from extension"""
```

**Brief Schema**:
```yaml
campaign_id: "campaign_001"
products:
  - product_id: "product_a"
    name: "Premium Coffee"
  - product_id: "product_b"
    name: "Organic Tea"
target_region: "US"
target_audience: "health-conscious millennials"
campaign_message: "Start your day right"
localization:  # optional
  language: "en"
  region_specific_message: "..."
```

### 3. Asset Manager

**Responsibility**: Manage asset storage, retrieval, and organization

**Interface**:
```python
class AssetManager:
    def __init__(self, input_dir: str, output_dir: str):
        """Initialize with input/output directories"""
        
    def get_asset(self, product_id: str) -> Optional[Image]:
        """Retrieve existing asset or return None"""
        
    def save_asset(self, product_id: str, aspect_ratio: str, 
                   image: Image, metadata: dict) -> str:
        """Save generated asset with metadata"""
        
    def organize_outputs(self, campaign_id: str) -> dict:
        """Organize outputs by product and aspect ratio"""
```

**Directory Structure**:
```
input_assets/
  ├── product_a.png
  └── product_b.jpg

output/
  └── campaign_001/
      ├── product_a/
      │   ├── 1x1_product_a.png
      │   ├── 9x16_product_a.png
      │   └── 16x9_product_a.png
      └── product_b/
          ├── 1x1_product_b.png
          ├── 9x16_product_b.png
          └── 16x9_product_b.png
```

### 4. GenAI Image Client

**Responsibility**: Interface with GenAI APIs for image generation

**Interface**:
```python
class GenAIClient:
    def __init__(self, provider: str, api_key: str):
        """Initialize with provider and credentials"""
        
    def generate_image(self, prompt: str, size: tuple) -> Image:
        """Generate image from text prompt"""
        
    def _build_prompt(self, product_name: str, audience: str, 
                      region: str) -> str:
        """Construct effective generation prompt"""
```

**Supported Providers**:
- OpenAI DALL-E 3 (primary)
- Stability AI (fallback)

**Prompt Engineering Strategy**:
- Include product name, target audience, and regional context
- Add style directives for advertising quality
- Specify composition requirements (product-focused, clean background)

### 5. Image Compositor

**Responsibility**: Create aspect ratio variants and apply text overlays

**Interface**:
```python
class ImageCompositor:
    def __init__(self, font_config: FontConfig):
        """Initialize with font configuration"""
        
    def create_variants(self, base_image: Image, 
                       aspect_ratios: List[str]) -> Dict[str, Image]:
        """Generate multiple aspect ratio versions"""
        
    def add_text_overlay(self, image: Image, text: str, 
                        position: str = "bottom") -> Image:
        """Add text overlay with proper styling"""
        
    def _smart_crop(self, image: Image, target_ratio: float) -> Image:
        """Intelligently crop to target aspect ratio"""
        
    def _ensure_contrast(self, image: Image, text_region: tuple) -> Image:
        """Add overlay or adjust to ensure text readability"""
```

**Aspect Ratio Handling**:
- **1:1 (Square)**: Center crop from base image
- **9:16 (Vertical/Stories)**: Crop to vertical orientation, prioritize top portion
- **16:9 (Horizontal/Feed)**: Crop to horizontal, maintain center focus

**Text Overlay Strategy**:
- Position text in bottom third of image
- Add semi-transparent overlay behind text for contrast
- Use brand-appropriate font (configurable)
- Scale font size based on image dimensions
- Support multi-line text wrapping

### 6. Compliance Checker (Optional)

**Responsibility**: Validate brand compliance and legal requirements

**Interface**:
```python
class ComplianceChecker:
    def __init__(self, brand_config: BrandConfig, 
                 legal_config: LegalConfig):
        """Initialize with compliance rules"""
        
    def check_brand_compliance(self, image: Image) -> ComplianceResult:
        """Verify logo presence and brand colors"""
        
    def check_legal_compliance(self, text: str) -> ComplianceResult:
        """Check for prohibited terms"""
        
    def _detect_logo(self, image: Image) -> bool:
        """Detect brand logo using template matching"""
        
    def _analyze_colors(self, image: Image) -> List[str]:
        """Extract dominant colors from image"""
```

**Brand Compliance Checks**:
- Logo detection using template matching
- Color palette validation against brand guidelines
- Minimum logo size requirements

**Legal Compliance Checks**:
- Prohibited word list matching
- Case-insensitive pattern matching
- Flagging with severity levels (warning vs. blocking)

### 7. Logger and Reporter

**Responsibility**: Track operations and generate execution reports

**Interface**:
```python
class PipelineLogger:
    def __init__(self, log_file: str):
        """Initialize logger with output file"""
        
    def log_operation(self, operation: str, status: str, 
                     details: dict):
        """Log individual operation"""
        
    def generate_report(self, results: List[OperationResult]) -> Report:
        """Generate summary report"""
```

**Report Contents**:
- Campaign ID and timestamp
- Products processed
- Assets reused vs. generated
- Success/failure status per output
- Compliance check results
- Total execution time
- Cost estimation (API calls)

## Data Models

### Core Data Structures

```python
@dataclass
class CampaignBrief:
    campaign_id: str
    products: List[Product]
    target_region: str
    target_audience: str
    campaign_message: str
    localization: Optional[Localization] = None

@dataclass
class Product:
    product_id: str
    name: str
    description: Optional[str] = None

@dataclass
class Localization:
    language: str
    region_specific_message: Optional[str] = None

@dataclass
class PipelineResult:
    campaign_id: str
    outputs: List[GeneratedAsset]
    execution_time: float
    success: bool
    errors: List[str]

@dataclass
class GeneratedAsset:
    product_id: str
    aspect_ratio: str
    file_path: str
    was_generated: bool  # True if GenAI, False if reused
    compliance_status: Optional[ComplianceResult] = None
```

## Error Handling

### Error Categories and Strategies

1. **Input Errors** (Brief parsing, missing fields)
   - Validate early and fail fast
   - Provide clear error messages with field names
   - Return non-zero exit code

2. **Asset Errors** (Missing files, corrupt images)
   - Attempt GenAI generation as fallback
   - Log warning if input asset unusable
   - Continue processing other products

3. **GenAI Errors** (API failures, rate limits, invalid responses)
   - Retry with exponential backoff (max 3 attempts)
   - Fall back to alternative provider if configured
   - Skip product if all generation attempts fail
   - Log detailed error for debugging

4. **Processing Errors** (Image manipulation failures)
   - Log error with stack trace
   - Skip affected variant
   - Continue with other aspect ratios

5. **Storage Errors** (Write permissions, disk space)
   - Fail entire pipeline execution
   - Preserve any successfully generated assets
   - Provide clear error message

### Logging Strategy

- **INFO**: Normal operations (asset reused, generation started)
- **WARNING**: Recoverable issues (missing input asset, using fallback)
- **ERROR**: Failed operations (generation failed, compliance violation)
- **DEBUG**: Detailed execution info (API calls, image dimensions)

## Testing Strategy

### Unit Testing

**Components to Test**:
- Brief Parser: Valid/invalid formats, missing fields
- Asset Manager: File operations, path handling
- Image Compositor: Aspect ratio calculations, text positioning
- Compliance Checker: Logo detection, color analysis, word matching

**Approach**:
- Use pytest framework
- Mock external dependencies (GenAI APIs, file I/O)
- Test edge cases (empty briefs, malformed images)
- Aim for 70%+ code coverage on core logic

### Integration Testing

**Scenarios**:
1. End-to-end pipeline with mock GenAI responses
2. Asset reuse vs. generation paths
3. Multiple products in single brief
4. All aspect ratios generated correctly
5. Text overlay applied properly

**Approach**:
- Use test fixtures for sample briefs and images
- Mock GenAI API calls to avoid costs
- Verify output directory structure
- Validate generated image properties

### Manual Testing

**Test Cases**:
1. Run with real GenAI API (small test)
2. Verify visual quality of outputs
3. Test with various image types (photos, illustrations)
4. Validate text readability across aspect ratios
5. Test compliance checks with known violations

## Configuration Management

### Configuration File Structure

```yaml
# config.yaml
genai:
  provider: "openai"  # or "stability"
  api_key: "${OPENAI_API_KEY}"  # from environment
  model: "dall-e-3"
  default_size: [1024, 1024]
  
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
  padding: 20
  background_opacity: 0.6
  
compliance:
  enabled: false
  brand:
    logo_template: "./brand/logo.png"
    brand_colors: ["#FF0000", "#0000FF"]
  legal:
    prohibited_words: ["guarantee", "free", "winner"]
    
logging:
  level: "INFO"
  file: "./pipeline.log"
```

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key
- `STABILITY_API_KEY`: Stability AI API key (optional)
- `PIPELINE_CONFIG`: Path to config file (default: ./config.yaml)

## Performance Considerations

### Optimization Strategies

1. **Parallel Processing**: Process multiple products concurrently using ThreadPoolExecutor
2. **Caching**: Cache GenAI responses to avoid regeneration during development
3. **Image Optimization**: Use appropriate compression for output files
4. **Lazy Loading**: Load images only when needed

### Expected Performance

- **Asset Reuse**: < 1 second per variant
- **GenAI Generation**: 10-30 seconds per image (API dependent)
- **Image Composition**: < 2 seconds per variant
- **Total Pipeline**: ~30-60 seconds for 2 products × 3 aspect ratios with generation

## Security Considerations

1. **API Key Management**: Store keys in environment variables, never in code
2. **Input Validation**: Sanitize all brief inputs to prevent injection
3. **File Path Validation**: Prevent directory traversal attacks
4. **Rate Limiting**: Implement client-side rate limiting for GenAI APIs
5. **Content Safety**: Use GenAI provider's content filtering features

## Deployment and Operations

### Installation Requirements

```bash
pip install pillow pyyaml openai stability-sdk requests
```

### Running the Pipeline

```bash
# Basic usage
python pipeline.py --brief campaign_brief.yaml

# With custom config
python pipeline.py --brief campaign_brief.yaml --config custom_config.yaml

# Enable compliance checks
python pipeline.py --brief campaign_brief.yaml --compliance

# Verbose logging
python pipeline.py --brief campaign_brief.yaml --verbose
```

### Output Artifacts

1. **Generated Images**: Organized in output directory
2. **Execution Log**: Detailed operation log
3. **Summary Report**: JSON report with statistics
4. **Compliance Report**: If compliance checks enabled

## Future Enhancements

1. **Multi-language Support**: Automatic translation of campaign messages
2. **A/B Variant Generation**: Generate multiple creative variants per product
3. **Video Support**: Extend to video asset generation
4. **Cloud Storage Integration**: Direct upload to Azure/AWS/Dropbox
5. **Web UI**: Browser-based interface for non-technical users
6. **Batch Processing**: Process multiple campaigns in single execution
7. **Performance Analytics**: Track which creatives perform best
8. **Template System**: Reusable design templates for consistency

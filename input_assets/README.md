# Input Assets Directory

This directory contains existing product images that the pipeline can reuse instead of generating new ones via GenAI.

## Naming Convention

Input asset filenames **must match** the `product_id` specified in your campaign brief.

### Format

```
{product_id}.{extension}
```

### Supported Extensions

- `.png` (recommended for best quality)
- `.jpg`
- `.jpeg`

### Examples

If your campaign brief contains:
```yaml
products:
  - product_id: "coffee_premium"
    name: "Premium Arabica Coffee"
  - product_id: "tea_organic"
    name: "Organic Green Tea"
```

Then your input assets should be named:
```
input_assets/
  ├── coffee_premium.png  (or .jpg/.jpeg)
  └── tea_organic.png     (or .jpg/.jpeg)
```

## How It Works

1. **Asset Exists**: If the pipeline finds a matching input asset, it will:
   - Reuse the existing image (no GenAI generation)
   - Create aspect ratio variants (1:1, 9:16, 16:9)
   - Apply text overlay
   - Save to output directory

2. **Asset Missing**: If no matching input asset is found, the pipeline will:
   - Generate a new image using OpenAI DALL-E 3
   - Use the product `name` and campaign context in the generation prompt
   - Create aspect ratio variants
   - Apply text overlay
   - Save to output directory

## Image Requirements

### Recommended Specifications

- **Format**: PNG (for transparency support and quality)
- **Minimum Size**: 1024x1024 pixels (for best quality across all aspect ratios)
- **Aspect Ratio**: Square (1:1) or landscape (16:9) work best
- **File Size**: Under 10MB for optimal processing speed
- **Color Mode**: RGB

### Content Guidelines

- **Product Focus**: Product should be clearly visible and centered
- **Clean Background**: Simple backgrounds work best for text overlay
- **High Quality**: Use high-resolution images to maintain quality after cropping
- **Lighting**: Well-lit images ensure better text contrast
- **Composition**: Leave space at the bottom for text overlay

## Sample Assets

To test the pipeline without input assets:

1. **Option 1**: Let GenAI generate images
   - Simply run the pipeline without placing files here
   - The system will automatically generate images for missing products

2. **Option 2**: Add your own product images
   - Place product photos following the naming convention above
   - Ensure they meet the recommended specifications

3. **Option 3**: Use placeholder images
   - Create simple placeholder images (e.g., colored squares with product names)
   - Useful for testing the pipeline flow without real assets

## Example Workflow

### With Existing Assets

```bash
# 1. Place your product images
cp ~/my_products/coffee.png input_assets/coffee_premium.png
cp ~/my_products/tea.png input_assets/tea_organic.png

# 2. Run the pipeline
python pipeline.py --brief examples/example_brief.yaml

# Result: Pipeline reuses your images, no GenAI generation needed
```

### Without Existing Assets

```bash
# 1. Ensure this directory is empty or missing the product files

# 2. Run the pipeline
python pipeline.py --brief examples/example_brief.yaml

# Result: Pipeline generates new images via DALL-E 3
```

## Cost Optimization

**Reusing input assets saves money!**

- GenAI generation cost: ~$0.04-0.08 per image (DALL-E 3)
- Asset reuse cost: $0.00

For campaigns with multiple runs or iterations, placing input assets here can significantly reduce API costs.

## Troubleshooting

### "Asset not found, generating new image"

This is normal behavior when no matching input asset exists. The pipeline will generate a new image.

### "Failed to load input asset"

Possible causes:
- File is corrupted or not a valid image format
- File permissions prevent reading
- Filename doesn't match product_id exactly (case-sensitive)

Solution: Verify the file is a valid image and the filename matches the product_id.

### "Image quality is poor after processing"

Possible causes:
- Input image resolution is too low
- Heavy compression in original image

Solution: Use higher resolution input images (minimum 1024x1024 recommended).

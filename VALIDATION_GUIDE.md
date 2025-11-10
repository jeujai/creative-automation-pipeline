# Pipeline Validation Guide

This guide provides step-by-step instructions for validating the Creative Automation Pipeline end-to-end.

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up OpenAI API key** (required for real GenAI tests):
   ```bash
   export OPENAI_API_KEY=your_openai_api_key_here
   ```

## Automated Validation

### Run Integration Tests

Run the automated validation script:

```bash
./validate_pipeline.sh
```

This will run all integration tests including:
- Asset reuse scenario (no API key needed)
- Text overlay validation (no API key needed)
- Real GenAI generation (requires API key)
- Mixed scenario (requires API key)

### Run Visual Quality Validation

After generating outputs, validate visual quality automatically:

```bash
python validate_visual_quality.py output/summer_sale_2024
```

This checks:
- Aspect ratios are mathematically correct
- Image dimensions are appropriate
- File sizes are reasonable
- Text overlay appears to be present
- Color modes are correct

## Manual Validation Steps

### Test 1: End-to-End with Real GenAI API

**Objective:** Verify complete pipeline with real image generation

**Steps:**

1. Ensure no input assets exist:
   ```bash
   rm -f input_assets/*.png input_assets/*.jpg
   ```

2. Run pipeline with example brief:
   ```bash
   python pipeline.py --brief examples/example_brief.yaml --verbose
   ```

3. **Verify execution:**
   - Pipeline should complete successfully
   - Console should show "Status: SUCCESS"
   - Should report 6 assets generated (2 products × 3 aspect ratios)
   - Execution time should be 30-90 seconds (depending on API)

4. **Verify output organization:**
   ```bash
   ls -R output/summer_sale_2024/
   ```
   
   Expected structure:
   ```
   output/summer_sale_2024/
   ├── coffee_premium/
   │   ├── 1x1_coffee_premium.png
   │   ├── 9x16_coffee_premium.png
   │   └── 16x9_coffee_premium.png
   └── tea_organic/
       ├── 1x1_tea_organic.png
       ├── 9x16_tea_organic.png
       └── 16x9_tea_organic.png
   ```

5. **Verify aspect ratios:**
   ```bash
   # Check image dimensions
   file output/summer_sale_2024/coffee_premium/*.png
   ```
   
   - 1x1 files should be square (e.g., 1024×1024)
   - 9x16 files should be vertical (e.g., 576×1024)
   - 16x9 files should be horizontal (e.g., 1024×576)

6. **Verify text overlay:**
   - Open each generated image
   - Verify "Start Your Day Right" text is visible
   - Text should be at bottom of image
   - Text should have good contrast/readability
   - Text should have semi-transparent background

7. **Check logs:**
   ```bash
   tail -50 pipeline.log
   ```
   
   Should show:
   - "Generating new asset" for both products
   - "Creating aspect ratio variants"
   - "Adding text overlay"
   - No ERROR messages

### Test 2: Asset Reuse Scenario

**Objective:** Verify pipeline reuses existing assets instead of regenerating

**Steps:**

1. Create mock input assets:
   ```bash
   # Create simple test images
   python -c "
   from PIL import Image
   img = Image.new('RGB', (1024, 1024), color='blue')
   img.save('input_assets/coffee_premium.png')
   img = Image.new('RGB', (1024, 1024), color='green')
   img.save('input_assets/tea_organic.png')
   "
   ```

2. Clean previous outputs:
   ```bash
   rm -rf output/summer_sale_2024/
   ```

3. Run pipeline:
   ```bash
   python pipeline.py --brief examples/example_brief.yaml --verbose
   ```

4. **Verify execution:**
   - Pipeline should complete in < 5 seconds (no API calls)
   - Console should show "Assets Generated: 6"
   - Should show "Reused: 6" (not generated)

5. **Verify logs show reuse:**
   ```bash
   grep "Reusing existing asset" pipeline.log
   ```
   
   Should show 2 lines (one for each product)

6. **Verify outputs exist:**
   - All 6 output files should be created
   - Images should be based on the blue/green input assets
   - Text overlay should still be applied

### Test 3: Mixed Scenario

**Objective:** Verify pipeline handles mix of existing and missing assets

**Steps:**

1. Keep only one input asset:
   ```bash
   rm -f input_assets/tea_organic.png
   # Keep coffee_premium.png from previous test
   ```

2. Clean outputs:
   ```bash
   rm -rf output/summer_sale_2024/
   ```

3. Run pipeline:
   ```bash
   python pipeline.py --brief examples/example_brief.yaml --verbose
   ```

4. **Verify execution:**
   - Should show "Generated: 3" (tea_organic variants)
   - Should show "Reused: 3" (coffee_premium variants)

5. **Verify logs:**
   ```bash
   grep -E "(Reusing|Generating)" pipeline.log | tail -2
   ```
   
   Should show:
   - "Reusing existing asset for product: coffee_premium"
   - "Generating new asset for product: tea_organic"

### Test 4: Compliance Checks (Optional)

**Objective:** Verify optional compliance features work

**Steps:**

1. Create brand logo template:
   ```bash
   python -c "
   from PIL import Image, ImageDraw
   img = Image.new('RGB', (100, 100), color='white')
   draw = ImageDraw.Draw(img)
   draw.rectangle([10, 10, 90, 90], fill='red')
   img.save('brand/logo.png')
   "
   ```

2. Enable compliance in config:
   ```bash
   # Edit config.yaml and set compliance.enabled: true
   sed -i.bak 's/enabled: false/enabled: true/' config.yaml
   ```

3. Run pipeline with compliance:
   ```bash
   python pipeline.py --brief examples/example_brief.yaml --compliance --verbose
   ```

4. **Verify compliance checks:**
   - Logs should show "Running compliance checks"
   - Should show brand compliance results
   - Should show legal compliance results

5. **Restore config:**
   ```bash
   mv config.yaml.bak config.yaml
   ```

## Visual Quality Review

For each generated image, manually verify:

1. **Image Quality:**
   - Images are clear and not pixelated
   - Colors are vibrant and appropriate
   - No obvious artifacts or distortions

2. **Aspect Ratio Quality:**
   - 1:1 (Square): Product centered, good composition
   - 9:16 (Vertical): Product visible in vertical frame
   - 16:9 (Horizontal): Product visible in horizontal frame
   - No awkward cropping that cuts off important elements

3. **Text Overlay Quality:**
   - Text is clearly readable on all variants
   - Text color contrasts well with background
   - Semi-transparent overlay provides good readability
   - Text doesn't obscure important product features
   - Text wraps appropriately if message is long

4. **Overall Creative Quality:**
   - Images look professional and ad-ready
   - Consistent style across all variants
   - Appropriate for target audience and region
   - Campaign message is prominent and clear

## Success Criteria

✅ All automated tests pass  
✅ Pipeline completes without errors  
✅ All 6 output files generated (2 products × 3 ratios)  
✅ Aspect ratios are mathematically correct  
✅ Text overlay is visible and readable on all images  
✅ Output directory structure matches specification  
✅ Asset reuse works correctly (no regeneration when assets exist)  
✅ Logging indicates reuse vs generation accurately  
✅ Visual quality meets professional standards  
✅ Text readability is good across all aspect ratios  

## Troubleshooting

### API Key Issues

If you see "GenAI API key not configured":
```bash
export OPENAI_API_KEY=your_key_here
```

### Permission Errors

If you see permission errors:
```bash
chmod +x validate_pipeline.sh
chmod -R 755 input_assets/ output/
```

### Missing Dependencies

If imports fail:
```bash
pip install -r requirements.txt
```

### Font Issues

If text overlay fails with font errors:
```bash
# On macOS, Arial should be available by default
# On Linux, install: sudo apt-get install ttf-mscorefonts-installer
```

## Performance Benchmarks

Expected performance metrics:

- **With GenAI generation:** 30-90 seconds for 2 products
- **With asset reuse:** < 5 seconds for 2 products
- **Per product generation:** 15-45 seconds (API dependent)
- **Per variant creation:** < 1 second
- **Text overlay:** < 0.5 seconds per image

## Cost Estimation

OpenAI DALL-E 3 pricing (as of 2024):
- Standard quality (1024×1024): $0.040 per image
- HD quality (1024×1024): $0.080 per image

For the example brief (2 products):
- Cost per run: ~$0.08 - $0.16
- With asset reuse: $0.00 (no API calls)

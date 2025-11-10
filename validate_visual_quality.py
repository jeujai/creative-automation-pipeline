#!/usr/bin/env python3
"""
Visual Quality Validation Script

This script performs automated checks on generated creative assets to validate
basic quality metrics like dimensions, file sizes, and aspect ratios.
"""

import sys
from pathlib import Path
from PIL import Image
import argparse


def validate_aspect_ratio(image_path: Path, expected_ratio: str) -> tuple:
    """
    Validate that an image has the correct aspect ratio.
    
    Args:
        image_path: Path to image file
        expected_ratio: Expected ratio as string (e.g., "1:1", "9:16", "16:9")
    
    Returns:
        Tuple of (passed: bool, message: str)
    """
    try:
        img = Image.open(image_path)
        width, height = img.size
        actual_ratio = width / height
        
        # Parse expected ratio
        ratio_parts = expected_ratio.split(':')
        expected_ratio_value = int(ratio_parts[0]) / int(ratio_parts[1])
        
        # Allow small tolerance for floating point comparison
        tolerance = 0.01
        ratio_diff = abs(actual_ratio - expected_ratio_value)
        
        if ratio_diff < tolerance:
            return True, f"✅ Aspect ratio correct: {width}×{height} ({actual_ratio:.3f})"
        else:
            return False, f"❌ Aspect ratio incorrect: {width}×{height} ({actual_ratio:.3f}), expected {expected_ratio_value:.3f}"
    
    except Exception as e:
        return False, f"❌ Error validating aspect ratio: {str(e)}"


def validate_image_quality(image_path: Path) -> tuple:
    """
    Validate basic image quality metrics.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Tuple of (passed: bool, message: str)
    """
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        issues = []
        
        # Check minimum dimensions
        if width < 500 or height < 500:
            issues.append(f"Image too small: {width}×{height}")
        
        # Check maximum dimensions (reasonable limit)
        if width > 2048 or height > 2048:
            issues.append(f"Image too large: {width}×{height}")
        
        # Check color mode
        if img.mode not in ['RGB', 'RGBA']:
            issues.append(f"Unexpected color mode: {img.mode}")
        
        # Check file size
        file_size = image_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb > 10:
            issues.append(f"File size too large: {file_size_mb:.2f}MB")
        
        if issues:
            return False, f"❌ Quality issues: {'; '.join(issues)}"
        else:
            return True, f"✅ Quality OK: {width}×{height}, {file_size_mb:.2f}MB, {img.mode}"
    
    except Exception as e:
        return False, f"❌ Error validating quality: {str(e)}"


def validate_text_overlay(image_path: Path) -> tuple:
    """
    Check if text overlay appears to be present (basic check).
    
    This is a simple heuristic check - it looks for variation in the bottom
    portion of the image which would indicate text overlay.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Tuple of (passed: bool, message: str)
    """
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        # Sample bottom 20% of image
        bottom_region = img.crop((0, int(height * 0.8), width, height))
        
        # Convert to grayscale and get pixel values
        gray = bottom_region.convert('L')
        pixels = list(gray.getdata())
        
        # Check for variation (text would create variation)
        min_val = min(pixels)
        max_val = max(pixels)
        variation = max_val - min_val
        
        # If there's significant variation, likely has text overlay
        if variation > 30:  # Threshold for detecting text
            return True, f"✅ Text overlay detected (variation: {variation})"
        else:
            return False, f"⚠️  Text overlay may be missing (low variation: {variation})"
    
    except Exception as e:
        return False, f"❌ Error checking text overlay: {str(e)}"


def validate_campaign_output(campaign_dir: Path) -> dict:
    """
    Validate all outputs for a campaign.
    
    Args:
        campaign_dir: Path to campaign output directory
    
    Returns:
        Dictionary with validation results
    """
    results = {
        'total_files': 0,
        'passed': 0,
        'failed': 0,
        'warnings': 0,
        'details': []
    }
    
    if not campaign_dir.exists():
        results['details'].append(f"❌ Campaign directory not found: {campaign_dir}")
        results['failed'] += 1
        return results
    
    # Expected aspect ratios
    aspect_ratios = {
        '1x1': '1:1',
        '9x16': '9:16',
        '16x9': '16:9'
    }
    
    # Find all product directories
    product_dirs = [d for d in campaign_dir.iterdir() if d.is_dir()]
    
    if not product_dirs:
        results['details'].append(f"❌ No product directories found in {campaign_dir}")
        results['failed'] += 1
        return results
    
    for product_dir in product_dirs:
        product_id = product_dir.name
        results['details'].append(f"\n📦 Product: {product_id}")
        
        # Check for all expected aspect ratios
        for ratio_prefix, ratio_value in aspect_ratios.items():
            # Find file with this ratio prefix
            files = list(product_dir.glob(f'{ratio_prefix}_*.png'))
            
            if not files:
                results['details'].append(f"  ❌ Missing {ratio_value} variant")
                results['failed'] += 1
                continue
            
            if len(files) > 1:
                results['details'].append(f"  ⚠️  Multiple files for {ratio_value}: {len(files)}")
                results['warnings'] += 1
            
            image_path = files[0]
            results['total_files'] += 1
            
            # Validate aspect ratio
            passed, message = validate_aspect_ratio(image_path, ratio_value)
            results['details'].append(f"  {message}")
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
                continue
            
            # Validate image quality
            passed, message = validate_image_quality(image_path)
            results['details'].append(f"  {message}")
            if not passed:
                results['failed'] += 1
                continue
            
            # Check for text overlay
            passed, message = validate_text_overlay(image_path)
            results['details'].append(f"  {message}")
            if not passed:
                results['warnings'] += 1
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate visual quality of generated creative assets'
    )
    parser.add_argument(
        'campaign_dir',
        type=str,
        help='Path to campaign output directory (e.g., output/summer_sale_2024)'
    )
    
    args = parser.parse_args()
    campaign_dir = Path(args.campaign_dir)
    
    print("="*70)
    print("VISUAL QUALITY VALIDATION")
    print("="*70)
    print(f"Campaign Directory: {campaign_dir}")
    print()
    
    # Run validation
    results = validate_campaign_output(campaign_dir)
    
    # Print results
    for detail in results['details']:
        print(detail)
    
    # Print summary
    print()
    print("="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Total Files Checked: {results['total_files']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Warnings: {results['warnings']}")
    print()
    
    if results['failed'] == 0:
        print("✅ VALIDATION PASSED - All quality checks passed!")
        print()
        print("Next Steps:")
        print("1. Perform manual visual review using VISUAL_QUALITY_CHECKLIST.md")
        print("2. Open images in image viewer and verify:")
        print("   - Text is clearly readable")
        print("   - Images look professional")
        print("   - Aspect ratios are visually correct")
        print("   - No obvious defects or artifacts")
        return 0
    else:
        print("❌ VALIDATION FAILED - Some quality checks failed")
        print()
        print("Please review the issues above and:")
        print("1. Fix any configuration or code issues")
        print("2. Re-run the pipeline")
        print("3. Run this validation script again")
        return 1


if __name__ == '__main__':
    sys.exit(main())

"""Unit tests for ImageCompositor."""

import pytest
from PIL import Image
from src.compositors.image_compositor import ImageCompositor


class TestImageCompositor:
    """Test suite for ImageCompositor class."""
    
    @pytest.fixture
    def compositor(self):
        """Create ImageCompositor instance for testing."""
        return ImageCompositor(
            font_family="Arial",
            font_size=48,
            text_color="#FFFFFF",
            text_position="bottom",
            padding=20,
            background_opacity=0.6
        )
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        # Create a 1000x1000 RGB image with gradient
        img = Image.new('RGB', (1000, 1000), color='blue')
        return img
    
    def test_create_variants_all_ratios(self, compositor, sample_image):
        """Test creating all standard aspect ratio variants."""
        variants = compositor.create_variants(sample_image)
        
        assert len(variants) == 3
        assert "1:1" in variants
        assert "9:16" in variants
        assert "16:9" in variants
        
        # Verify each variant is an Image
        for ratio, img in variants.items():
            assert isinstance(img, Image.Image)
    
    def test_create_variants_specific_ratios(self, compositor, sample_image):
        """Test creating specific aspect ratio variants."""
        variants = compositor.create_variants(sample_image, ["1:1", "16:9"])
        
        assert len(variants) == 2
        assert "1:1" in variants
        assert "16:9" in variants
        assert "9:16" not in variants
    
    def test_aspect_ratio_1_1_dimensions(self, compositor, sample_image):
        """Test 1:1 aspect ratio produces square image."""
        variants = compositor.create_variants(sample_image, ["1:1"])
        square = variants["1:1"]
        
        width, height = square.size
        assert width == height
        assert width <= 1000  # Should not exceed original
    
    def test_aspect_ratio_9_16_dimensions(self, compositor, sample_image):
        """Test 9:16 aspect ratio produces correct vertical dimensions."""
        variants = compositor.create_variants(sample_image, ["9:16"])
        vertical = variants["9:16"]
        
        width, height = vertical.size
        ratio = width / height
        expected_ratio = 9 / 16
        
        # Allow small floating point tolerance
        assert abs(ratio - expected_ratio) < 0.01
    
    def test_aspect_ratio_16_9_dimensions(self, compositor, sample_image):
        """Test 16:9 aspect ratio produces correct horizontal dimensions."""
        variants = compositor.create_variants(sample_image, ["16:9"])
        horizontal = variants["16:9"]
        
        width, height = horizontal.size
        ratio = width / height
        expected_ratio = 16 / 9
        
        # Allow small floating point tolerance
        assert abs(ratio - expected_ratio) < 0.01
    
    def test_create_variants_invalid_ratio(self, compositor, sample_image):
        """Test that invalid aspect ratio raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported aspect ratio"):
            compositor.create_variants(sample_image, ["4:3"])
    
    def test_add_text_overlay_returns_image(self, compositor, sample_image):
        """Test that add_text_overlay returns an Image."""
        result = compositor.add_text_overlay(sample_image, "Test Message")
        
        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size
    
    def test_add_text_overlay_does_not_modify_original(self, compositor, sample_image):
        """Test that original image is not modified."""
        original_mode = sample_image.mode
        compositor.add_text_overlay(sample_image, "Test Message")
        
        # Original should remain unchanged
        assert sample_image.mode == original_mode
    
    def test_add_text_overlay_different_positions(self, compositor, sample_image):
        """Test text overlay at different positions."""
        positions = ["bottom", "top", "center"]
        
        for pos in positions:
            result = compositor.add_text_overlay(sample_image, "Test", position=pos)
            assert isinstance(result, Image.Image)
    
    def test_text_wrapping_long_message(self, compositor, sample_image):
        """Test that long text messages are wrapped."""
        long_text = "This is a very long message that should be wrapped across multiple lines"
        result = compositor.add_text_overlay(sample_image, long_text)
        
        assert isinstance(result, Image.Image)
    
    def test_font_size_scaling_small_image(self, compositor):
        """Test font size scales down for smaller images."""
        small_img = Image.new('RGB', (200, 200), color='blue')
        font_size = compositor._calculate_font_size(200, 200)
        
        # Should be smaller than base size for small image
        assert font_size < compositor.base_font_size
        assert font_size >= 20  # Minimum bound
    
    def test_font_size_scaling_large_image(self, compositor):
        """Test font size scales up for larger images."""
        large_img = Image.new('RGB', (2000, 2000), color='blue')
        font_size = compositor._calculate_font_size(2000, 2000)
        
        # Should be larger than base size for large image
        assert font_size > compositor.base_font_size
        assert font_size <= 120  # Maximum bound
    
    def test_add_text_overlay_with_contrast(self, compositor, sample_image):
        """Test contrast-adjusted text overlay."""
        result = compositor.add_text_overlay_with_contrast(sample_image, "Test Message")
        
        assert isinstance(result, Image.Image)
        assert result.size == sample_image.size
    
    def test_ensure_contrast_bright_region(self, compositor):
        """Test contrast adjustment for bright regions."""
        bright_img = Image.new('RGB', (500, 500), color='white')
        text_region = (100, 100, 400, 200)
        
        adjusted_opacity = compositor._ensure_contrast(bright_img, text_region)
        
        # Bright regions should increase opacity
        assert adjusted_opacity > compositor.background_opacity
    
    def test_ensure_contrast_dark_region(self, compositor):
        """Test contrast adjustment for dark regions."""
        dark_img = Image.new('RGB', (500, 500), color='black')
        text_region = (100, 100, 400, 200)
        
        adjusted_opacity = compositor._ensure_contrast(dark_img, text_region)
        
        # Dark regions should decrease opacity
        assert adjusted_opacity < compositor.background_opacity
    
    def test_smart_crop_wider_image(self, compositor):
        """Test smart crop on wider image."""
        wide_img = Image.new('RGB', (2000, 1000), color='blue')
        cropped = compositor._smart_crop(wide_img, 1.0, "1:1")
        
        width, height = cropped.size
        assert width == height
        assert width == 1000  # Should match shorter dimension
    
    def test_smart_crop_taller_image(self, compositor):
        """Test smart crop on taller image."""
        tall_img = Image.new('RGB', (1000, 2000), color='blue')
        cropped = compositor._smart_crop(tall_img, 1.0, "1:1")
        
        width, height = cropped.size
        assert width == height
        assert width == 1000  # Should match shorter dimension
    
    def test_create_variants_various_sizes(self, compositor):
        """Test creating variants with various image sizes."""
        sizes = [(800, 600), (1920, 1080), (1080, 1920), (500, 500)]
        
        for size in sizes:
            img = Image.new('RGB', size, color='green')
            variants = compositor.create_variants(img)
            
            assert len(variants) == 3
            for ratio_str, variant in variants.items():
                width, height = variant.size
                expected_ratio = compositor.ASPECT_RATIOS[ratio_str]
                actual_ratio = width / height
                assert abs(actual_ratio - expected_ratio) < 0.01

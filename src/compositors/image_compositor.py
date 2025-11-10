"""Image compositor for creating aspect ratio variants and text overlays."""

from PIL import Image, ImageDraw, ImageFont, ImageStat
from typing import Dict, Tuple, Optional
import os


class ImageCompositor:
    """Handles image composition including aspect ratio variants and text overlays."""
    
    # Standard aspect ratios
    ASPECT_RATIOS = {
        "1:1": 1.0,
        "9:16": 9/16,
        "16:9": 16/9
    }
    
    def __init__(self, font_family: str = "Arial", font_size: int = 48, 
                 text_color: str = "#FFFFFF", text_position: str = "bottom",
                 padding: int = 20, background_opacity: float = 0.6):
        """
        Initialize ImageCompositor with text overlay configuration.
        
        Args:
            font_family: Font family name for text overlay
            font_size: Base font size (will be scaled based on image dimensions)
            text_color: Hex color code for text
            text_position: Position for text overlay ("bottom", "top", "center")
            padding: Padding around text in pixels
            background_opacity: Opacity of text background overlay (0.0-1.0)
        """
        self.font_family = font_family
        self.base_font_size = font_size
        self.text_color = text_color
        self.text_position = text_position
        self.padding = padding
        self.background_opacity = background_opacity
    
    def create_variants(self, base_image: Image.Image, 
                       aspect_ratios: list = None) -> Dict[str, Image.Image]:
        """
        Generate multiple aspect ratio versions of the base image.
        
        Args:
            base_image: Source image to create variants from
            aspect_ratios: List of aspect ratio strings (e.g., ["1:1", "9:16", "16:9"])
                          If None, generates all standard ratios
        
        Returns:
            Dictionary mapping aspect ratio string to cropped image
        """
        if aspect_ratios is None:
            aspect_ratios = list(self.ASPECT_RATIOS.keys())
        
        variants = {}
        for ratio_str in aspect_ratios:
            if ratio_str not in self.ASPECT_RATIOS:
                raise ValueError(f"Unsupported aspect ratio: {ratio_str}")
            
            target_ratio = self.ASPECT_RATIOS[ratio_str]
            cropped = self._smart_crop(base_image, target_ratio, ratio_str)
            variants[ratio_str] = cropped
        
        return variants
    
    def _smart_crop(self, image: Image.Image, target_ratio: float, 
                    ratio_str: str) -> Image.Image:
        """
        Intelligently crop image to target aspect ratio.
        
        Strategy:
        - 1:1 (Square): Center crop
        - 9:16 (Vertical): Top-focused crop for portrait orientation
        - 16:9 (Horizontal): Center crop for landscape orientation
        
        Args:
            image: Source image
            target_ratio: Target width/height ratio
            ratio_str: Aspect ratio string for strategy selection
        
        Returns:
            Cropped image with high-quality resampling
        """
        img_width, img_height = image.size
        current_ratio = img_width / img_height
        
        # Determine crop dimensions
        if current_ratio > target_ratio:
            # Image is wider than target - crop width
            new_width = int(img_height * target_ratio)
            new_height = img_height
        else:
            # Image is taller than target - crop height
            new_width = img_width
            new_height = int(img_width / target_ratio)
        
        # Calculate crop box based on aspect ratio strategy
        if ratio_str == "1:1":
            # Center crop for square
            left = (img_width - new_width) // 2
            top = (img_height - new_height) // 2
        elif ratio_str == "9:16":
            # Top-focused crop for vertical/stories
            left = (img_width - new_width) // 2
            top = int((img_height - new_height) * 0.3)  # Focus on upper 30%
        elif ratio_str == "16:9":
            # Center crop for horizontal/feed
            left = (img_width - new_width) // 2
            top = (img_height - new_height) // 2
        else:
            # Default to center crop
            left = (img_width - new_width) // 2
            top = (img_height - new_height) // 2
        
        right = left + new_width
        bottom = top + new_height
        
        # Perform crop with high-quality resampling
        cropped = image.crop((left, top, right, bottom))
        
        return cropped

    def add_text_overlay(self, image: Image.Image, text: str, 
                        position: Optional[str] = None) -> Image.Image:
        """
        Add text overlay with semi-transparent background to image.
        
        Args:
            image: Image to add text overlay to
            text: Text message to overlay
            position: Override default text position ("bottom", "top", "center")
        
        Returns:
            New image with text overlay applied
        """
        # Create a copy to avoid modifying original
        img_copy = image.copy()
        
        # Use provided position or default
        pos = position if position else self.text_position
        
        # Scale font size based on image dimensions
        img_width, img_height = img_copy.size
        scaled_font_size = self._calculate_font_size(img_width, img_height)
        
        # Load font
        font = self._load_font(scaled_font_size)
        
        # Wrap text if needed
        wrapped_text = self._wrap_text(text, font, img_width - (self.padding * 2))
        
        # Calculate text dimensions
        draw = ImageDraw.Draw(img_copy)
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate text position
        text_x = (img_width - text_width) // 2
        
        if pos == "bottom":
            text_y = img_height - text_height - self.padding * 2
        elif pos == "top":
            text_y = self.padding * 2
        else:  # center
            text_y = (img_height - text_height) // 2
        
        # Create semi-transparent overlay for text background
        overlay = Image.new('RGBA', img_copy.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Draw background rectangle
        bg_padding = self.padding
        bg_left = text_x - bg_padding
        bg_top = text_y - bg_padding
        bg_right = text_x + text_width + bg_padding
        bg_bottom = text_y + text_height + bg_padding
        
        bg_alpha = int(self.background_opacity * 255)
        overlay_draw.rectangle(
            [(bg_left, bg_top), (bg_right, bg_bottom)],
            fill=(0, 0, 0, bg_alpha)
        )
        
        # Composite overlay onto image
        if img_copy.mode != 'RGBA':
            img_copy = img_copy.convert('RGBA')
        img_copy = Image.alpha_composite(img_copy, overlay)
        
        # Draw text on top
        draw = ImageDraw.Draw(img_copy)
        draw.multiline_text(
            (text_x, text_y),
            wrapped_text,
            font=font,
            fill=self.text_color,
            align='center'
        )
        
        return img_copy
    
    def _calculate_font_size(self, img_width: int, img_height: int) -> int:
        """
        Calculate appropriate font size based on image dimensions.
        
        Args:
            img_width: Image width in pixels
            img_height: Image height in pixels
        
        Returns:
            Scaled font size
        """
        # Scale font size as percentage of image height
        # Base size is for ~1000px height, scale proportionally
        scale_factor = img_height / 1000.0
        scaled_size = int(self.base_font_size * scale_factor)
        
        # Ensure minimum and maximum bounds
        return max(20, min(scaled_size, 120))
    
    def _load_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        """
        Load font with specified size.
        
        Args:
            font_size: Font size in points
        
        Returns:
            Font object, falls back to default if specified font not available
        """
        try:
            # Try to load specified font
            font = ImageFont.truetype(self.font_family, font_size)
        except (OSError, IOError):
            # Try common font paths
            common_fonts = [
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
                "C:\\Windows\\Fonts\\arial.ttf",  # Windows
                "Arial.ttf",
                "Helvetica.ttf"
            ]
            
            font = None
            for font_path in common_fonts:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                    break
                except (OSError, IOError):
                    continue
            
            # Fall back to default font if nothing works
            if font is None:
                font = ImageFont.load_default()
        
        return font
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, 
                   max_width: int) -> str:
        """
        Wrap text to fit within maximum width.
        
        Args:
            text: Text to wrap
            font: Font to use for measuring
            max_width: Maximum width in pixels
        
        Returns:
            Text with newlines inserted for wrapping
        """
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Use a temporary draw object to measure text
            temp_img = Image.new('RGB', (1, 1))
            draw = ImageDraw.Draw(temp_img)
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)

    def _ensure_contrast(self, image: Image.Image, text_region: Tuple[int, int, int, int]) -> float:
        """
        Analyze text region brightness and adjust overlay opacity for sufficient contrast.
        
        Args:
            image: Image to analyze
            text_region: Tuple of (left, top, right, bottom) defining text area
        
        Returns:
            Adjusted opacity value (0.0-1.0) to ensure text readability
        """
        # Crop to text region
        region = image.crop(text_region)
        
        # Convert to grayscale for brightness analysis
        if region.mode != 'L':
            region = region.convert('L')
        
        # Calculate average brightness (0-255)
        stat = ImageStat.Stat(region)
        avg_brightness = stat.mean[0]
        
        # Adjust opacity based on brightness
        # Bright regions need darker overlay, dark regions need lighter overlay
        if avg_brightness > 180:
            # Very bright - need strong dark overlay
            adjusted_opacity = min(self.background_opacity + 0.3, 0.9)
        elif avg_brightness > 120:
            # Moderately bright - increase overlay slightly
            adjusted_opacity = min(self.background_opacity + 0.15, 0.8)
        elif avg_brightness < 60:
            # Very dark - reduce overlay or use lighter background
            adjusted_opacity = max(self.background_opacity - 0.2, 0.3)
        else:
            # Good contrast - use default
            adjusted_opacity = self.background_opacity
        
        return adjusted_opacity
    
    def add_text_overlay_with_contrast(self, image: Image.Image, text: str,
                                       position: Optional[str] = None) -> Image.Image:
        """
        Add text overlay with automatic contrast adjustment.
        
        This method analyzes the text region brightness and adjusts the overlay
        opacity to ensure sufficient contrast for readability.
        
        Args:
            image: Image to add text overlay to
            text: Text message to overlay
            position: Override default text position ("bottom", "top", "center")
        
        Returns:
            New image with contrast-adjusted text overlay
        """
        # Create a copy to avoid modifying original
        img_copy = image.copy()
        
        # Use provided position or default
        pos = position if position else self.text_position
        
        # Scale font size based on image dimensions
        img_width, img_height = img_copy.size
        scaled_font_size = self._calculate_font_size(img_width, img_height)
        
        # Load font
        font = self._load_font(scaled_font_size)
        
        # Wrap text if needed
        wrapped_text = self._wrap_text(text, font, img_width - (self.padding * 2))
        
        # Calculate text dimensions
        draw = ImageDraw.Draw(img_copy)
        bbox = draw.multiline_textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate text position
        text_x = (img_width - text_width) // 2
        
        if pos == "bottom":
            text_y = img_height - text_height - self.padding * 2
        elif pos == "top":
            text_y = self.padding * 2
        else:  # center
            text_y = (img_height - text_height) // 2
        
        # Define text region for contrast analysis
        bg_padding = self.padding
        text_region = (
            max(0, text_x - bg_padding),
            max(0, text_y - bg_padding),
            min(img_width, text_x + text_width + bg_padding),
            min(img_height, text_y + text_height + bg_padding)
        )
        
        # Analyze and adjust contrast
        adjusted_opacity = self._ensure_contrast(img_copy, text_region)
        
        # Create semi-transparent overlay with adjusted opacity
        overlay = Image.new('RGBA', img_copy.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Draw background rectangle with adjusted opacity
        bg_left = text_x - bg_padding
        bg_top = text_y - bg_padding
        bg_right = text_x + text_width + bg_padding
        bg_bottom = text_y + text_height + bg_padding
        
        bg_alpha = int(adjusted_opacity * 255)
        overlay_draw.rectangle(
            [(bg_left, bg_top), (bg_right, bg_bottom)],
            fill=(0, 0, 0, bg_alpha)
        )
        
        # Composite overlay onto image
        if img_copy.mode != 'RGBA':
            img_copy = img_copy.convert('RGBA')
        img_copy = Image.alpha_composite(img_copy, overlay)
        
        # Draw text on top
        draw = ImageDraw.Draw(img_copy)
        draw.multiline_text(
            (text_x, text_y),
            wrapped_text,
            font=font,
            fill=self.text_color,
            align='center'
        )
        
        return img_copy

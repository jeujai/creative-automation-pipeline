"""Compliance checker for brand and legal validation."""

import re
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
import numpy as np
import cv2

from src.models import ComplianceResult


class BrandConfig:
    """Configuration for brand compliance checks."""
    
    def __init__(self, logo_template_path: Optional[str] = None, 
                 brand_colors: Optional[List[str]] = None,
                 min_logo_confidence: float = 0.7):
        """
        Initialize brand configuration.
        
        Args:
            logo_template_path: Path to brand logo template image
            brand_colors: List of brand colors in hex format (e.g., ["#FF0000", "#0000FF"])
            min_logo_confidence: Minimum confidence threshold for logo detection (0.0-1.0)
        """
        self.logo_template_path = logo_template_path
        self.brand_colors = brand_colors or []
        self.min_logo_confidence = min_logo_confidence
        self._logo_template = None
        
    def load_logo_template(self) -> Optional[np.ndarray]:
        """Load and cache the logo template."""
        if self._logo_template is None and self.logo_template_path:
            if Path(self.logo_template_path).exists():
                template_img = Image.open(self.logo_template_path)
                self._logo_template = cv2.cvtColor(np.array(template_img), cv2.COLOR_RGB2BGR)
        return self._logo_template


class LegalConfig:
    """Configuration for legal compliance checks."""
    
    def __init__(self, prohibited_words: Optional[List[str]] = None,
                 severity_levels: Optional[dict] = None):
        """
        Initialize legal configuration.
        
        Args:
            prohibited_words: List of prohibited terms
            severity_levels: Dict mapping words to severity ("warning" or "blocking")
        """
        self.prohibited_words = prohibited_words or []
        self.severity_levels = severity_levels or {}


class ComplianceChecker:
    """Validates brand compliance and legal requirements for creative assets."""
    
    def __init__(self, brand_config: Optional[BrandConfig] = None,
                 legal_config: Optional[LegalConfig] = None):
        """
        Initialize compliance checker with configuration.
        
        Args:
            brand_config: Brand compliance configuration
            legal_config: Legal compliance configuration
        """
        self.brand_config = brand_config or BrandConfig()
        self.legal_config = legal_config or LegalConfig()
    
    def check_brand_compliance(self, image: Image.Image) -> ComplianceResult:
        """
        Verify logo presence and brand colors in the image.
        
        Args:
            image: PIL Image to check for brand compliance
            
        Returns:
            ComplianceResult with pass/fail status and details
        """
        violations = []
        details_parts = []
        
        # Check logo presence
        logo_detected = self._detect_logo(image)
        if self.brand_config.logo_template_path:
            if logo_detected:
                details_parts.append("Logo detected in image")
            else:
                violations.append("Brand logo not detected in image")
                details_parts.append("Logo detection failed")
        
        # Check brand colors
        if self.brand_config.brand_colors:
            colors_present = self._analyze_colors(image)
            brand_colors_found = any(
                self._color_match(color, brand_color)
                for color in colors_present
                for brand_color in self.brand_config.brand_colors
            )
            
            if brand_colors_found:
                details_parts.append(f"Brand colors detected: {', '.join(self.brand_config.brand_colors)}")
            else:
                violations.append(f"Brand colors not found. Expected: {', '.join(self.brand_config.brand_colors)}")
                details_parts.append("Brand color validation failed")
        
        passed = len(violations) == 0
        details = "; ".join(details_parts) if details_parts else "No brand compliance checks configured"
        
        return ComplianceResult(
            passed=passed,
            details=details,
            violations=violations
        )
    
    def check_legal_compliance(self, text: str) -> ComplianceResult:
        """
        Check for prohibited terms in campaign text.
        
        Args:
            text: Campaign message text to check
            
        Returns:
            ComplianceResult with pass/fail status and details
        """
        violations = []
        details_parts = []
        
        if not self.legal_config.prohibited_words:
            return ComplianceResult(
                passed=True,
                details="No prohibited words configured",
                violations=[]
            )
        
        # Case-insensitive pattern matching
        text_lower = text.lower()
        
        for word in self.legal_config.prohibited_words:
            # Use word boundaries to match whole words
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            if re.search(pattern, text_lower):
                severity = self.legal_config.severity_levels.get(word, "warning")
                violation_msg = f"Prohibited word '{word}' found (severity: {severity})"
                violations.append(violation_msg)
        
        if violations:
            details_parts.append(f"Found {len(violations)} prohibited term(s)")
            passed = False
        else:
            details_parts.append(f"No prohibited terms found (checked {len(self.legal_config.prohibited_words)} terms)")
            passed = True
        
        details = "; ".join(details_parts)
        
        return ComplianceResult(
            passed=passed,
            details=details,
            violations=violations
        )
    
    def _detect_logo(self, image: Image.Image) -> bool:
        """
        Detect brand logo using template matching.
        
        Args:
            image: PIL Image to search for logo
            
        Returns:
            True if logo detected with sufficient confidence, False otherwise
        """
        if not self.brand_config.logo_template_path:
            return False
        
        template = self.brand_config.load_logo_template()
        if template is None:
            return False
        
        # Convert PIL image to OpenCV format
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Perform template matching
        result = cv2.matchTemplate(img_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # Check if confidence exceeds threshold
        return max_val >= self.brand_config.min_logo_confidence
    
    def _analyze_colors(self, image: Image.Image) -> List[str]:
        """
        Extract dominant colors from image.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            List of dominant colors in hex format
        """
        # Resize image for faster processing
        img_small = image.copy()
        img_small.thumbnail((100, 100))
        
        # Convert to RGB if needed
        if img_small.mode != 'RGB':
            img_small = img_small.convert('RGB')
        
        # Get pixel data
        pixels = np.array(img_small)
        pixels = pixels.reshape(-1, 3)
        
        # Use k-means clustering to find dominant colors
        from sklearn.cluster import KMeans
        
        n_colors = 5
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Convert cluster centers to hex colors
        dominant_colors = []
        for center in kmeans.cluster_centers_:
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(center[0]), int(center[1]), int(center[2])
            )
            dominant_colors.append(hex_color.upper())
        
        return dominant_colors
    
    def _color_match(self, color1: str, color2: str, tolerance: int = 30) -> bool:
        """
        Check if two hex colors match within tolerance.
        
        Args:
            color1: First hex color (e.g., "#FF0000")
            color2: Second hex color (e.g., "#FF0000")
            tolerance: RGB distance tolerance (0-255)
            
        Returns:
            True if colors match within tolerance
        """
        # Remove '#' and convert to RGB
        rgb1 = tuple(int(color1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        rgb2 = tuple(int(color2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        # Calculate Euclidean distance
        distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))
        
        return bool(distance <= tolerance)

"""Base GenAI client interface for image generation."""

from abc import ABC, abstractmethod
from typing import Tuple
from PIL import Image


class GenAIClient(ABC):
    """Abstract base class for GenAI image generation clients."""
    
    def __init__(self, api_key: str):
        """
        Initialize the GenAI client.
        
        Args:
            api_key: API key for the GenAI service
        """
        self.api_key = api_key
    
    @abstractmethod
    def generate_image(self, prompt: str, size: Tuple[int, int] = (1024, 1024)) -> Image.Image:
        """
        Generate an image from a text prompt.
        
        Args:
            prompt: Text description for image generation
            size: Target image size as (width, height) tuple
            
        Returns:
            PIL Image object
            
        Raises:
            Exception: If generation fails after retries
        """
        pass
    
    def _build_prompt(self, product_name: str, audience: str, region: str) -> str:
        """
        Construct an effective generation prompt with context.
        
        Args:
            product_name: Name of the product
            audience: Target audience description
            region: Target region/market
            
        Returns:
            Formatted prompt string
        """
        prompt = (
            f"Create a high-quality advertising image for {product_name}. "
            f"Target audience: {audience}. "
            f"Market: {region}. "
            f"Style: professional product photography with clean background, "
            f"product-focused composition, suitable for social media advertising."
        )
        return prompt

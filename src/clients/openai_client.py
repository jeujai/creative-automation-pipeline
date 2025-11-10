"""OpenAI DALL-E 3 implementation of GenAI client."""

import time
import requests
from io import BytesIO
from typing import Tuple
from PIL import Image
import openai

from .genai_client import GenAIClient


class OpenAIClient(GenAIClient):
    """OpenAI DALL-E 3 client for image generation."""
    
    def __init__(self, api_key: str, model: str = "dall-e-3"):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: dall-e-3)
        """
        super().__init__(api_key)
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
        self.max_retries = 3
        self.base_delay = 2  # seconds
    
    def generate_image(self, prompt: str, size: Tuple[int, int] = (1024, 1024)) -> Image.Image:
        """
        Generate an image using DALL-E 3.
        
        Args:
            prompt: Text description for image generation
            size: Target image size (DALL-E 3 supports 1024x1024, 1024x1792, 1792x1024)
            
        Returns:
            PIL Image object
            
        Raises:
            Exception: If generation fails after all retries
        """
        # Convert size tuple to DALL-E 3 format string
        size_str = self._format_size(size)
        
        for attempt in range(self.max_retries):
            try:
                # Call DALL-E 3 API
                response = self.client.images.generate(
                    model=self.model,
                    prompt=prompt,
                    size=size_str,
                    quality="standard",
                    n=1
                )
                
                # Extract image URL from response
                image_url = response.data[0].url
                
                # Download and convert to PIL Image
                image = self._download_image(image_url)
                
                return image
                
            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    delay = self._calculate_backoff(attempt)
                    print(f"Rate limit hit. Retrying in {delay}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    raise Exception(f"Rate limit exceeded after {self.max_retries} attempts: {str(e)}")
                    
            except openai.APIError as e:
                if attempt < self.max_retries - 1:
                    delay = self._calculate_backoff(attempt)
                    print(f"API error occurred. Retrying in {delay}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    raise Exception(f"API error after {self.max_retries} attempts: {str(e)}")
                    
            except openai.APIConnectionError as e:
                if attempt < self.max_retries - 1:
                    delay = self._calculate_backoff(attempt)
                    print(f"Network error. Retrying in {delay}s... (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    raise Exception(f"Network error after {self.max_retries} attempts: {str(e)}")
                    
            except Exception as e:
                # For unexpected errors, don't retry
                raise Exception(f"Unexpected error during image generation: {str(e)}")
        
        raise Exception(f"Failed to generate image after {self.max_retries} attempts")
    
    def _download_image(self, url: str) -> Image.Image:
        """
        Download image from URL and convert to PIL Image.
        
        Args:
            url: Image URL from API response
            
        Returns:
            PIL Image object
            
        Raises:
            Exception: If download fails
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            image_data = BytesIO(response.content)
            image = Image.open(image_data)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            return image
            
        except requests.RequestException as e:
            raise Exception(f"Failed to download image: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to process downloaded image: {str(e)}")
    
    def _format_size(self, size: Tuple[int, int]) -> str:
        """
        Format size tuple to DALL-E 3 compatible string.
        
        DALL-E 3 supports: 1024x1024, 1024x1792, 1792x1024
        
        Args:
            size: (width, height) tuple
            
        Returns:
            Size string in format "WIDTHxHEIGHT"
        """
        width, height = size
        
        # Map to closest supported size
        if width == height:
            return "1024x1024"
        elif width < height:
            return "1024x1792"
        else:
            return "1792x1024"
    
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        return self.base_delay * (2 ** attempt)

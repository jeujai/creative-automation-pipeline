"""Google Imagen GenAI client for image generation."""

import time
import io
import base64
from typing import Tuple
from PIL import Image

try:
    from google.cloud import aiplatform
    from vertexai.preview.vision_models import ImageGenerationModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

from src.clients.genai_client import GenAIClient


class ImagenClient(GenAIClient):
    """Google Imagen 3 implementation of GenAI client."""
    
    def __init__(self, api_key: str, model: str = "imagen-3.0-generate-001", 
                 max_retries: int = 3, retry_delay: int = 2,
                 project_id: str = None, location: str = "us-central1"):
        """
        Initialize Imagen client.
        
        Args:
            api_key: Google API key (or use Application Default Credentials)
            model: Imagen model to use (default: imagen-3.0-generate-001)
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            project_id: Google Cloud project ID
            location: Google Cloud region
        """
        super().__init__(api_key)
        self.model_name = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.project_id = project_id
        self.location = location
        
        if not VERTEX_AVAILABLE:
            raise ImportError(
                "Google Cloud Vertex AI SDK not installed. "
                "Install with: pip install google-cloud-aiplatform"
            )
        
        # Initialize Vertex AI
        if project_id:
            aiplatform.init(project=project_id, location=location)
        
        self.model = ImageGenerationModel.from_pretrained(model)
    
    def generate_image(self, prompt: str, size: Tuple[int, int] = (1024, 1024)) -> Image.Image:
        """
        Generate an image using Google Imagen 3.
        
        Args:
            prompt: Text description for image generation
            size: Target image size as (width, height) tuple
            
        Returns:
            PIL Image object
            
        Raises:
            Exception: If generation fails after retries
        """
        # Enhance prompt for better image generation
        enhanced_prompt = self._enhance_prompt_for_imagen(prompt, size)
        
        last_error = None
        delay = self.retry_delay
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Generate image using Imagen
                # Imagen supports various aspect ratios
                aspect_ratio = self._get_aspect_ratio_string(size)
                
                response = self.model.generate_images(
                    prompt=enhanced_prompt,
                    number_of_images=1,
                    aspect_ratio=aspect_ratio,
                    safety_filter_level="block_some",
                    person_generation="allow_adult",
                )
                
                # Get the first generated image
                if response.images:
                    image_bytes = response.images[0]._image_bytes
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Resize to exact size if needed
                    if image.size != size:
                        image = image.resize(size, Image.Resampling.LANCZOS)
                    
                    return image
                else:
                    raise Exception("No images generated in response")
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    print(f"API error occurred. Retrying in {delay}s... (attempt {attempt}/{self.max_retries})")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    raise Exception(f"API error after {self.max_retries} attempts: {str(last_error)}")
    
    def _get_aspect_ratio_string(self, size: Tuple[int, int]) -> str:
        """
        Convert size tuple to Imagen aspect ratio string.
        
        Args:
            size: Target image size as (width, height)
            
        Returns:
            Aspect ratio string for Imagen API
        """
        aspect_ratio = size[0] / size[1]
        
        # Imagen supports: 1:1, 9:16, 16:9, 4:3, 3:4
        if abs(aspect_ratio - 1.0) < 0.1:
            return "1:1"
        elif abs(aspect_ratio - 9/16) < 0.1:
            return "9:16"
        elif abs(aspect_ratio - 16/9) < 0.1:
            return "16:9"
        elif abs(aspect_ratio - 4/3) < 0.1:
            return "4:3"
        elif abs(aspect_ratio - 3/4) < 0.1:
            return "3:4"
        else:
            # Default to closest match
            if aspect_ratio < 1.0:
                return "9:16"  # Vertical
            else:
                return "16:9"  # Horizontal
    
    def _enhance_prompt_for_imagen(self, prompt: str, size: Tuple[int, int]) -> str:
        """
        Enhance prompt specifically for Imagen's capabilities.
        
        Args:
            prompt: Original prompt
            size: Target image size
            
        Returns:
            Enhanced prompt string
        """
        aspect_ratio = size[0] / size[1]
        
        if abs(aspect_ratio - 1.0) < 0.1:
            ratio_desc = "square composition"
        elif aspect_ratio < 1.0:
            ratio_desc = "vertical portrait composition"
        else:
            ratio_desc = "horizontal landscape composition"
        
        enhanced = (
            f"{prompt} "
            f"High quality, professional photography, {ratio_desc}, "
            f"vibrant colors, sharp details, photorealistic, suitable for advertising."
        )
        
        return enhanced

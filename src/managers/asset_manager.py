"""Asset Manager for storage operations."""

import os
from pathlib import Path
from typing import Optional, Dict
from PIL import Image


class AssetManager:
    """Manages asset storage, retrieval, and organization."""
    
    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg'}
    
    def __init__(self, input_dir: str, output_dir: str):
        """
        Initialize AssetManager with input and output directories.
        
        Args:
            input_dir: Directory containing input product assets
            output_dir: Directory for saving generated outputs
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_asset(self, product_id: str) -> Optional[Image.Image]:
        """
        Retrieve existing asset for a product or return None.
        
        Checks for asset files with supported formats (PNG, JPG, JPEG).
        
        Args:
            product_id: Product identifier to look up
            
        Returns:
            PIL Image object if asset exists, None otherwise
        """
        # Try each supported format
        for ext in self.SUPPORTED_FORMATS:
            asset_path = self.input_dir / f"{product_id}{ext}"
            if asset_path.exists() and asset_path.is_file():
                try:
                    image = Image.open(asset_path)
                    # Load image data to ensure it's valid
                    image.load()
                    return image
                except Exception as e:
                    # If image is corrupt or unreadable, continue to next format
                    print(f"Warning: Could not load asset {asset_path}: {e}")
                    continue
        
        return None
    
    def save_asset(
        self,
        campaign_id: str,
        product_id: str,
        aspect_ratio: str,
        image: Image.Image,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save generated asset with organized directory structure.
        
        Creates directory structure: output/{campaign_id}/{product_id}/
        Filename format: {aspect_ratio}_{product_id}.png
        
        Args:
            campaign_id: Campaign identifier
            product_id: Product identifier
            aspect_ratio: Aspect ratio (e.g., "1x1", "9x16", "16x9")
            image: PIL Image object to save
            metadata: Optional metadata dictionary (for future use)
            
        Returns:
            Full path to saved file
        """
        # Create directory structure
        product_dir = self.output_dir / campaign_id / product_id
        product_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        filename = self._generate_filename(product_id, aspect_ratio)
        file_path = product_dir / filename
        
        # Save image with high quality
        image.save(file_path, format='PNG', optimize=True)
        
        return str(file_path)
    
    def organize_outputs(self, campaign_id: str) -> Dict[str, list]:
        """
        Organize and retrieve information about outputs for a campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Dictionary mapping product_ids to lists of output file paths
        """
        campaign_dir = self.output_dir / campaign_id
        
        if not campaign_dir.exists():
            return {}
        
        outputs = {}
        
        # Iterate through product directories
        for product_dir in campaign_dir.iterdir():
            if product_dir.is_dir():
                product_id = product_dir.name
                product_files = []
                
                # Collect all image files in product directory
                for file_path in product_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                        product_files.append(str(file_path))
                
                if product_files:
                    outputs[product_id] = sorted(product_files)
        
        return outputs
    
    def _generate_filename(self, product_id: str, aspect_ratio: str) -> str:
        """
        Generate clear, descriptive filename with aspect ratio prefix.
        
        Args:
            product_id: Product identifier
            aspect_ratio: Aspect ratio (e.g., "1x1", "9x16", "16x9")
            
        Returns:
            Filename string
        """
        # Normalize aspect ratio format (ensure it uses 'x' separator)
        normalized_ratio = aspect_ratio.replace(':', 'x').lower()
        return f"{normalized_ratio}_{product_id}.png"

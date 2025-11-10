"""Campaign brief parser for JSON and YAML formats."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any

from src.models import CampaignBrief, Product, Localization


class BriefParser:
    """Parser for campaign brief files in JSON or YAML format."""

    @staticmethod
    def parse(file_path: str) -> CampaignBrief:
        """
        Parse a campaign brief file.
        
        Args:
            file_path: Path to the brief file (JSON or YAML)
            
        Returns:
            CampaignBrief object
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is unsupported or content is invalid
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Brief file not found: {file_path}")
        
        # Detect format and parse
        file_format = BriefParser._detect_format(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_format == 'json':
                    data = json.load(f)
                elif file_format == 'yaml':
                    data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        
        # Validate and convert to CampaignBrief
        return BriefParser._dict_to_brief(data)

    @staticmethod
    def _detect_format(file_path: str) -> str:
        """
        Detect file format from extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Format string ('json' or 'yaml')
            
        Raises:
            ValueError: If the extension is not supported
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.json':
            return 'json'
        elif extension in ['.yaml', '.yml']:
            return 'yaml'
        else:
            raise ValueError(
                f"Unsupported file extension: {extension}. "
                "Supported formats: .json, .yaml, .yml"
            )

    @staticmethod
    def _dict_to_brief(data: Dict[str, Any]) -> CampaignBrief:
        """
        Convert dictionary to CampaignBrief object with validation.
        
        Args:
            data: Dictionary containing brief data
            
        Returns:
            CampaignBrief object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required top-level fields
        required_fields = [
            'campaign_id',
            'products',
            'target_region',
            'target_audience',
            'campaign_message'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Parse products
        products_data = data.get('products', [])
        if not products_data:
            raise ValueError("At least one product is required")
        
        products = []
        for idx, product_data in enumerate(products_data):
            if not isinstance(product_data, dict):
                raise ValueError(f"Product at index {idx} must be a dictionary")
            
            if 'product_id' not in product_data:
                raise ValueError(f"Product at index {idx} missing 'product_id'")
            if 'name' not in product_data:
                raise ValueError(f"Product at index {idx} missing 'name'")
            
            products.append(Product(
                product_id=product_data['product_id'],
                name=product_data['name'],
                description=product_data.get('description')
            ))
        
        # Parse optional localization
        localization = None
        if 'localization' in data:
            loc_data = data['localization']
            if not isinstance(loc_data, dict):
                raise ValueError("Localization must be a dictionary")
            
            if 'language' not in loc_data:
                raise ValueError("Localization missing 'language' field")
            
            localization = Localization(
                language=loc_data['language'],
                region_specific_message=loc_data.get('region_specific_message')
            )
        
        # Create and validate CampaignBrief
        brief = CampaignBrief(
            campaign_id=data['campaign_id'],
            products=products,
            target_region=data['target_region'],
            target_audience=data['target_audience'],
            campaign_message=data['campaign_message'],
            localization=localization
        )
        
        # Run validation
        brief.validate()
        
        return brief

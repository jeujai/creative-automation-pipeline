"""Data models for the Creative Automation Pipeline."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Product:
    """Represents a product in a campaign."""
    product_id: str
    name: str
    description: Optional[str] = None

    def validate(self) -> None:
        """Validate required fields are present."""
        if not self.product_id:
            raise ValueError("Product product_id is required")
        if not self.name:
            raise ValueError("Product name is required")


@dataclass
class Localization:
    """Represents localization settings for a campaign."""
    language: str
    region_specific_message: Optional[str] = None

    def validate(self) -> None:
        """Validate required fields are present."""
        if not self.language:
            raise ValueError("Localization language is required")


@dataclass
class CampaignBrief:
    """Represents a campaign brief with all necessary information."""
    campaign_id: str
    products: List[Product]
    target_region: str
    target_audience: str
    campaign_message: str
    localization: Optional[Localization] = None

    def validate(self) -> None:
        """Validate required fields are present and valid."""
        if not self.campaign_id:
            raise ValueError("campaign_id is required")
        if not self.products:
            raise ValueError("At least one product is required")
        if not self.target_region:
            raise ValueError("target_region is required")
        if not self.target_audience:
            raise ValueError("target_audience is required")
        if not self.campaign_message:
            raise ValueError("campaign_message is required")
        
        # Validate each product
        for product in self.products:
            product.validate()
        
        # Validate localization if present
        if self.localization:
            self.localization.validate()


@dataclass
class ComplianceResult:
    """Represents the result of a compliance check."""
    passed: bool
    details: str
    violations: List[str] = field(default_factory=list)


@dataclass
class GeneratedAsset:
    """Represents a generated creative asset."""
    product_id: str
    aspect_ratio: str
    file_path: str
    was_generated: bool  # True if GenAI generated, False if reused
    compliance_status: Optional[ComplianceResult] = None

    def validate(self) -> None:
        """Validate required fields are present."""
        if not self.product_id:
            raise ValueError("GeneratedAsset product_id is required")
        if not self.aspect_ratio:
            raise ValueError("GeneratedAsset aspect_ratio is required")
        if not self.file_path:
            raise ValueError("GeneratedAsset file_path is required")


@dataclass
class PipelineResult:
    """Represents the result of a pipeline execution."""
    campaign_id: str
    outputs: List[GeneratedAsset]
    execution_time: float
    success: bool
    errors: List[str] = field(default_factory=list)

    def validate(self) -> None:
        """Validate required fields are present."""
        if not self.campaign_id:
            raise ValueError("PipelineResult campaign_id is required")
        if self.outputs is None:
            raise ValueError("PipelineResult outputs is required")
        if self.execution_time < 0:
            raise ValueError("PipelineResult execution_time must be non-negative")
        
        # Validate each generated asset
        for asset in self.outputs:
            asset.validate()

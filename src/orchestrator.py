"""Pipeline orchestrator for coordinating creative asset generation."""

import time
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from src.models import CampaignBrief, PipelineResult, GeneratedAsset
from src.parsers.brief_parser import BriefParser
from src.managers.asset_manager import AssetManager
from src.clients.genai_client import GenAIClient
from src.compositors.image_compositor import ImageCompositor
from src.utils.logger import PipelineLogger
from src.utils.reporter import PipelineReporter


class PipelineOrchestrator:
    """Orchestrates the entire creative automation pipeline."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the pipeline orchestrator with configuration.
        
        Args:
            config: Configuration dictionary containing:
                - storage: input_dir, output_dir
                - genai: provider, api_key, model
                - aspect_ratios: list of aspect ratios to generate
                - text_overlay: font settings
                - logging: level, file
                - compliance: enabled, settings (optional)
        """
        self.config = config
        
        # Initialize logger
        log_config = config.get('logging', {})
        self.logger = PipelineLogger(
            log_file=log_config.get('file'),
            level=log_config.get('level', 'INFO')
        )
        
        # Initialize components
        storage_config = config.get('storage', {})
        self.asset_manager = AssetManager(
            input_dir=storage_config.get('input_dir', './input_assets'),
            output_dir=storage_config.get('output_dir', './output')
        )
        
        # Initialize GenAI client
        genai_config = config.get('genai', {})
        self.genai_client = self._initialize_genai_client(genai_config)
        
        # Initialize image compositor
        text_config = config.get('text_overlay', {})
        self.compositor = ImageCompositor(
            font_family=text_config.get('font_family', 'Arial'),
            font_size=text_config.get('font_size', 48),
            text_color=text_config.get('color', '#FFFFFF'),
            text_position=text_config.get('position', 'bottom'),
            padding=text_config.get('padding', 20),
            background_opacity=text_config.get('background_opacity', 0.6)
        )
        
        # Get aspect ratios to generate
        self.aspect_ratios = config.get('aspect_ratios', ['1:1', '9:16', '16:9'])
        
        # Compliance checker (optional)
        self.compliance_checker = None
        if config.get('compliance', {}).get('enabled', False):
            try:
                from src.compliance.checker import ComplianceChecker, BrandConfig, LegalConfig
                
                # Initialize brand config
                brand_dict = config['compliance'].get('brand', {})
                brand_config = BrandConfig(
                    logo_template_path=brand_dict.get('logo_template'),
                    brand_colors=brand_dict.get('brand_colors', []),
                    min_logo_confidence=brand_dict.get('min_logo_confidence', 0.7)
                )
                
                # Initialize legal config
                legal_dict = config['compliance'].get('legal', {})
                legal_config = LegalConfig(
                    prohibited_words=legal_dict.get('prohibited_words', []),
                    severity_levels=legal_dict.get('severity_levels', {})
                )
                
                self.compliance_checker = ComplianceChecker(
                    brand_config=brand_config,
                    legal_config=legal_config
                )
                self.logger.info("Compliance checking enabled")
            except ImportError:
                self.logger.warning("Compliance module not available")
    
    def _initialize_genai_client(self, genai_config: Dict[str, Any]) -> Optional[GenAIClient]:
        """
        Initialize the GenAI client based on configuration.
        
        Args:
            genai_config: GenAI configuration dictionary
        
        Returns:
            GenAIClient instance or None if not configured
        """
        provider = genai_config.get('provider', 'openai').lower()
        api_key = genai_config.get('api_key')
        
        if not api_key:
            self.logger.warning("No GenAI API key configured - generation will fail if assets are missing")
            return None
        
        if provider == 'openai':
            from src.clients.openai_client import OpenAIClient
            model = genai_config.get('model', 'dall-e-3')
            return OpenAIClient(api_key=api_key, model=model)
        elif provider == 'imagen' or provider == 'google':
            from src.clients.gemini_client import ImagenClient
            model = genai_config.get('model', 'imagen-3.0-generate-001')
            project_id = genai_config.get('project_id')
            location = genai_config.get('location', 'us-central1')
            return ImagenClient(
                api_key=api_key, 
                model=model,
                project_id=project_id,
                location=location
            )
        else:
            raise ValueError(f"Unsupported GenAI provider: {provider}")
    
    def run(self, brief_path: str) -> PipelineResult:
        """
        Execute the pipeline for a given campaign brief.
        
        Args:
            brief_path: Path to campaign brief file (JSON or YAML)
        
        Returns:
            PipelineResult containing execution details
        """
        start_time = datetime.now()
        errors = []
        outputs = []
        
        self.logger.info(f"Starting pipeline execution for brief: {brief_path}")
        
        try:
            # Parse campaign brief
            self.logger.info("Parsing campaign brief...")
            brief = BriefParser.parse(brief_path)
            
            # Validate brief
            if not self._validate_brief(brief):
                raise ValueError("Campaign brief validation failed")
            
            self.logger.info(f"Processing campaign: {brief.campaign_id}")
            self.logger.info(f"Products to process: {len(brief.products)}")
            
            # Process each product
            for product in brief.products:
                try:
                    self.logger.info(f"Processing product: {product.product_id} ({product.name})")
                    product_outputs = self._process_product(brief, product)
                    outputs.extend(product_outputs)
                    self.logger.log_operation(
                        f"Product {product.product_id}",
                        "success",
                        {"assets_generated": len(product_outputs)}
                    )
                except Exception as e:
                    error_msg = f"Failed to process product {product.product_id}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
                    # Continue processing other products
                    continue
            
            # Calculate execution time
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Create result
            success = len(outputs) > 0 and len(errors) == 0
            result = PipelineResult(
                campaign_id=brief.campaign_id,
                outputs=outputs,
                execution_time=execution_time,
                success=success,
                errors=errors
            )
            
            # Generate report
            self.logger.info("Generating execution report...")
            report_path = Path(self.asset_manager.output_dir) / brief.campaign_id / "report.json"
            report = PipelineReporter.generate_report(
                result=result,
                start_time=start_time,
                end_time=end_time,
                output_path=str(report_path)
            )
            
            # Log summary
            summary = PipelineReporter.format_summary(report)
            self.logger.info("\n" + summary)
            
            return result
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return PipelineResult(
                campaign_id="unknown",
                outputs=outputs,
                execution_time=execution_time,
                success=False,
                errors=errors
            )
    
    def _validate_brief(self, brief: CampaignBrief) -> bool:
        """
        Validate campaign brief structure and required fields.
        
        Args:
            brief: CampaignBrief to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            brief.validate()
            
            # Additional validation
            if len(brief.products) == 0:
                self.logger.error("Campaign brief must contain at least one product")
                return False
            
            self.logger.info("Campaign brief validation passed")
            return True
            
        except ValueError as e:
            self.logger.error(f"Brief validation failed: {str(e)}")
            return False
    
    def _process_product(self, brief: CampaignBrief, product) -> list:
        """
        Process a single product through the pipeline.
        
        Args:
            brief: CampaignBrief containing campaign details
            product: Product to process
        
        Returns:
            List of GeneratedAsset objects
        
        Raises:
            Exception: If processing fails
        """
        outputs = []
        
        # Step 1: Check for existing asset or generate new one
        self.logger.info(f"Checking for existing asset: {product.product_id}")
        hero_image = self.asset_manager.get_asset(product.product_id)
        was_generated = False
        
        if hero_image:
            self.logger.log_operation(
                f"Asset for {product.product_id}",
                "reused",
                {"source": "input_assets"}
            )
        else:
            # Generate new asset using GenAI
            self.logger.info(f"No existing asset found, generating with GenAI...")
            
            if not self.genai_client:
                raise Exception("GenAI client not configured - cannot generate missing asset")
            
            # Build prompt
            prompt = self.genai_client._build_prompt(
                product_name=product.name,
                audience=brief.target_audience,
                region=brief.target_region
            )
            
            self.logger.debug(f"Generation prompt: {prompt}")
            
            # Generate image
            hero_image = self.genai_client.generate_image(prompt)
            was_generated = True
            
            self.logger.log_operation(
                f"Asset for {product.product_id}",
                "generated",
                {"provider": self.config.get('genai', {}).get('provider', 'openai')}
            )
        
        # Step 2: Create aspect ratio variants
        self.logger.info(f"Creating aspect ratio variants: {', '.join(self.aspect_ratios)}")
        variants = self.compositor.create_variants(hero_image, self.aspect_ratios)
        
        # Step 3: Apply text overlay to each variant
        campaign_message = brief.campaign_message
        if brief.localization and brief.localization.region_specific_message:
            campaign_message = brief.localization.region_specific_message
        
        self.logger.info(f"Applying text overlay: '{campaign_message}'")
        
        for aspect_ratio, variant_image in variants.items():
            # Add text overlay
            final_image = self.compositor.add_text_overlay(variant_image, campaign_message)
            
            # Step 4: Save output
            file_path = self.asset_manager.save_asset(
                campaign_id=brief.campaign_id,
                product_id=product.product_id,
                aspect_ratio=aspect_ratio.replace(':', 'x'),
                image=final_image
            )
            
            # Step 5: Optional compliance check
            compliance_status = None
            if self.compliance_checker:
                try:
                    compliance_status = self.compliance_checker.check_brand_compliance(final_image)
                    legal_status = self.compliance_checker.check_legal_compliance(campaign_message)
                    
                    # Combine results
                    if not legal_status.passed:
                        compliance_status.passed = False
                        compliance_status.violations.extend(legal_status.violations)
                    
                    self.logger.log_operation(
                        f"Compliance check for {product.product_id} ({aspect_ratio})",
                        "passed" if compliance_status.passed else "failed",
                        {"violations": len(compliance_status.violations)}
                    )
                except Exception as e:
                    self.logger.warning(f"Compliance check failed: {str(e)}")
            
            # Create GeneratedAsset record
            asset = GeneratedAsset(
                product_id=product.product_id,
                aspect_ratio=aspect_ratio,
                file_path=file_path,
                was_generated=was_generated,
                compliance_status=compliance_status
            )
            outputs.append(asset)
            
            self.logger.info(f"Saved: {file_path}")
        
        return outputs

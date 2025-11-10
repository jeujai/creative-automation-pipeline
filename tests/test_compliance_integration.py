"""
Integration tests for compliance checking features.

These tests validate the optional brand and legal compliance checking
functionality when enabled in the pipeline.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageDraw
import yaml

from src.orchestrator import PipelineOrchestrator


class TestComplianceIntegration:
    """Integration tests for compliance features."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = tempfile.mkdtemp()
        input_dir = Path(temp_dir) / "input_assets"
        output_dir = Path(temp_dir) / "output"
        brand_dir = Path(temp_dir) / "brand"
        input_dir.mkdir()
        output_dir.mkdir()
        brand_dir.mkdir()
        
        yield {
            'base': temp_dir,
            'input': str(input_dir),
            'output': str(output_dir),
            'brand': str(brand_dir)
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def compliance_config(self, temp_dirs):
        """Create test configuration with compliance enabled."""
        logo_path = Path(temp_dirs['brand']) / 'logo.png'
        
        # Create a simple logo template
        logo = Image.new('RGB', (100, 100), color='white')
        draw = ImageDraw.Draw(logo)
        draw.rectangle([10, 10, 90, 90], fill='red')
        logo.save(logo_path)
        
        return {
            'genai': {
                'provider': 'openai',
                'api_key': os.environ.get('OPENAI_API_KEY', 'test_key'),
                'model': 'dall-e-3',
                'default_size': [1024, 1024],
                'max_retries': 3,
                'retry_delay': 2
            },
            'storage': {
                'input_dir': temp_dirs['input'],
                'output_dir': temp_dirs['output'],
                'supported_formats': ['png', 'jpg', 'jpeg']
            },
            'aspect_ratios': ['1:1', '9:16', '16:9'],
            'text_overlay': {
                'font_family': 'Arial',
                'font_size': 48,
                'color': '#FFFFFF',
                'position': 'bottom',
                'padding': 20,
                'background_opacity': 0.6,
                'max_width_ratio': 0.9,
                'line_spacing': 1.2
            },
            'compliance': {
                'enabled': True,
                'brand': {
                    'logo_template': str(logo_path),
                    'brand_colors': ['#FF0000', '#0000FF'],
                    'min_logo_size': [50, 50],
                    'color_tolerance': 30
                },
                'legal': {
                    'prohibited_words': ['guarantee', 'free', 'winner'],
                    'case_sensitive': False
                }
            },
            'logging': {
                'level': 'INFO',
                'file': str(Path(temp_dirs['base']) / 'test.log'),
                'console_output': False,
                'include_timestamp': True
            }
        }
    
    @pytest.fixture
    def compliant_brief(self, temp_dirs):
        """Create a compliant campaign brief."""
        brief_path = Path(temp_dirs['base']) / 'compliant_brief.yaml'
        brief_data = {
            'campaign_id': 'compliant_campaign',
            'products': [
                {
                    'product_id': 'product_compliant',
                    'name': 'Compliant Product',
                    'description': 'A product with compliant messaging'
                }
            ],
            'target_region': 'US',
            'target_audience': 'general audience',
            'campaign_message': 'Great Quality Product',  # No prohibited words
            'localization': {
                'language': 'en'
            }
        }
        
        with open(brief_path, 'w') as f:
            yaml.dump(brief_data, f)
        
        return str(brief_path)
    
    @pytest.fixture
    def non_compliant_brief(self, temp_dirs):
        """Create a non-compliant campaign brief with prohibited words."""
        brief_path = Path(temp_dirs['base']) / 'non_compliant_brief.yaml'
        brief_data = {
            'campaign_id': 'non_compliant_campaign',
            'products': [
                {
                    'product_id': 'product_non_compliant',
                    'name': 'Non-Compliant Product',
                    'description': 'A product with problematic messaging'
                }
            ],
            'target_region': 'US',
            'target_audience': 'general audience',
            'campaign_message': 'Free Guarantee - You are a Winner!',  # Contains prohibited words
            'localization': {
                'language': 'en'
            }
        }
        
        with open(brief_path, 'w') as f:
            yaml.dump(brief_data, f)
        
        return str(brief_path)
    
    def test_compliance_with_compliant_content(self, compliance_config, compliant_brief, temp_dirs):
        """
        Test compliance checking with compliant content.
        
        Verifies that compliance checking runs and produces results.
        Note: Logo detection may not pass with simple test images due to
        template matching sensitivity, but we verify the system runs.
        """
        # Create input asset with brand colors
        input_dir = Path(temp_dirs['input'])
        
        # Create image with brand colors (red and blue)
        img = Image.new('RGB', (1024, 1024), color='blue')
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 150, 150], fill='red')  # Red square
        img.save(input_dir / 'product_compliant.png')
        
        # Initialize orchestrator with compliance enabled
        orchestrator = PipelineOrchestrator(compliance_config)
        
        # Run pipeline
        result = orchestrator.run(compliant_brief)
        
        # Verify execution success
        assert result.success, f"Pipeline failed: {result.errors}"
        
        # Verify compliance results are present
        for asset in result.outputs:
            assert asset.compliance_status is not None
            
            # Verify compliance result has expected structure
            assert hasattr(asset.compliance_status, 'passed')
            assert hasattr(asset.compliance_status, 'details')
            assert hasattr(asset.compliance_status, 'violations')
            
            # Verify details mention brand colors (should be detected)
            assert 'Brand colors detected' in asset.compliance_status.details
    
    def test_compliance_with_non_compliant_content(self, compliance_config, non_compliant_brief, temp_dirs):
        """
        Test compliance checking with non-compliant content.
        
        Verifies that non-compliant content is properly flagged.
        """
        # Create input asset without brand logo
        input_dir = Path(temp_dirs['input'])
        
        # Create image without logo (just solid color)
        img = Image.new('RGB', (1024, 1024), color='green')
        img.save(input_dir / 'product_non_compliant.png')
        
        # Initialize orchestrator with compliance enabled
        orchestrator = PipelineOrchestrator(compliance_config)
        
        # Run pipeline
        result = orchestrator.run(non_compliant_brief)
        
        # Pipeline should still succeed (compliance doesn't block execution)
        assert result.success
        
        # Verify compliance results show violations
        for asset in result.outputs:
            assert asset.compliance_status is not None
            
            # Compliance should fail (prohibited words present)
            assert asset.compliance_status.passed is False
            
            # Should have violations listed
            assert len(asset.compliance_status.violations) > 0
            
            # Violations should mention prohibited words
            violation_text = ' '.join(asset.compliance_status.violations).lower()
            assert any(word in violation_text for word in ['free', 'guarantee', 'winner'])
    
    def test_compliance_disabled(self, compliance_config, compliant_brief, temp_dirs):
        """
        Test that compliance checks are skipped when disabled.
        """
        # Disable compliance
        compliance_config['compliance']['enabled'] = False
        
        # Create input asset
        input_dir = Path(temp_dirs['input'])
        img = Image.new('RGB', (1024, 1024), color='blue')
        img.save(input_dir / 'product_compliant.png')
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(compliance_config)
        
        # Run pipeline
        result = orchestrator.run(compliant_brief)
        
        # Verify execution success
        assert result.success
        
        # Verify compliance status is None (not checked)
        for asset in result.outputs:
            assert asset.compliance_status is None
    
    def test_compliance_report_generation(self, compliance_config, non_compliant_brief, temp_dirs):
        """
        Test that compliance reports are properly generated.
        """
        # Create input asset
        input_dir = Path(temp_dirs['input'])
        img = Image.new('RGB', (1024, 1024), color='yellow')
        img.save(input_dir / 'product_non_compliant.png')
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(compliance_config)
        
        # Run pipeline
        result = orchestrator.run(non_compliant_brief)
        
        # Verify execution success
        assert result.success
        
        # Check that compliance information is in the result
        assert len(result.outputs) > 0
        
        # Verify each output has compliance status
        for asset in result.outputs:
            compliance = asset.compliance_status
            assert compliance is not None
            
            # Verify compliance result structure
            assert hasattr(compliance, 'passed')
            assert hasattr(compliance, 'details')
            assert hasattr(compliance, 'violations')
            
            # Verify violations are detailed
            if not compliance.passed:
                assert len(compliance.violations) > 0
    
    def test_compliance_with_mixed_results(self, compliance_config, temp_dirs):
        """
        Test compliance with mixed compliant/non-compliant products.
        """
        # Create brief with multiple products
        brief_path = Path(temp_dirs['base']) / 'mixed_brief.yaml'
        brief_data = {
            'campaign_id': 'mixed_campaign',
            'products': [
                {
                    'product_id': 'product_good',
                    'name': 'Good Product',
                },
                {
                    'product_id': 'product_bad',
                    'name': 'Bad Product',
                }
            ],
            'target_region': 'US',
            'target_audience': 'general audience',
            'campaign_message': 'Free Winner Guarantee',  # Non-compliant
        }
        
        with open(brief_path, 'w') as f:
            yaml.dump(brief_data, f)
        
        # Create input assets
        input_dir = Path(temp_dirs['input'])
        for product_id in ['product_good', 'product_bad']:
            img = Image.new('RGB', (1024, 1024), color='purple')
            img.save(input_dir / f'{product_id}.png')
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(compliance_config)
        
        # Run pipeline
        result = orchestrator.run(str(brief_path))
        
        # Verify execution success
        assert result.success
        
        # All assets should have same compliance status (same message)
        compliance_statuses = [a.compliance_status.passed for a in result.outputs]
        assert all(status == compliance_statuses[0] for status in compliance_statuses)
        
        # Should be non-compliant due to prohibited words
        assert compliance_statuses[0] is False
        
        # All should have violations
        for asset in result.outputs:
            assert len(asset.compliance_status.violations) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

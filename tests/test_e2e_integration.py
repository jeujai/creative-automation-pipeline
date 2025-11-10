"""
End-to-end integration tests for the Creative Automation Pipeline.

These tests validate the complete pipeline flow from brief parsing through
asset generation and output organization.
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import yaml
import json

from src.orchestrator import PipelineOrchestrator
from src.parsers.brief_parser import BriefParser


class TestEndToEndIntegration:
    """End-to-end integration tests for the pipeline."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        temp_dir = tempfile.mkdtemp()
        input_dir = Path(temp_dir) / "input_assets"
        output_dir = Path(temp_dir) / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        yield {
            'base': temp_dir,
            'input': str(input_dir),
            'output': str(output_dir)
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_config(self, temp_dirs):
        """Create test configuration."""
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
                'enabled': False
            },
            'logging': {
                'level': 'INFO',
                'file': str(Path(temp_dirs['base']) / 'test.log'),
                'console_output': False,
                'include_timestamp': True
            }
        }
    
    @pytest.fixture
    def test_brief_yaml(self, temp_dirs):
        """Create test campaign brief in YAML format."""
        brief_path = Path(temp_dirs['base']) / 'test_brief.yaml'
        brief_data = {
            'campaign_id': 'test_campaign_e2e',
            'products': [
                {
                    'product_id': 'product_test_a',
                    'name': 'Test Product A',
                    'description': 'First test product'
                },
                {
                    'product_id': 'product_test_b',
                    'name': 'Test Product B',
                    'description': 'Second test product'
                }
            ],
            'target_region': 'US',
            'target_audience': 'test audience',
            'campaign_message': 'Test Campaign Message',
            'localization': {
                'language': 'en'
            }
        }
        
        with open(brief_path, 'w') as f:
            yaml.dump(brief_data, f)
        
        return str(brief_path)
    
    def test_e2e_with_asset_generation(self, test_config, test_brief_yaml, temp_dirs):
        """
        Test end-to-end pipeline with GenAI asset generation.
        
        This test requires OPENAI_API_KEY to be set in environment.
        If not set, the test will be skipped.
        """
        if not os.environ.get('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set - skipping real API test")
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(test_config)
        
        # Run pipeline
        result = orchestrator.run(test_brief_yaml)
        
        # Verify execution success
        assert result.success, f"Pipeline failed: {result.errors}"
        assert result.campaign_id == 'test_campaign_e2e'
        assert result.execution_time > 0
        
        # Verify outputs generated
        # 2 products × 3 aspect ratios = 6 total outputs
        assert len(result.outputs) == 6
        
        # Verify all assets were generated (not reused)
        for asset in result.outputs:
            assert asset.was_generated is True
        
        # Verify output organization
        output_dir = Path(temp_dirs['output']) / 'test_campaign_e2e'
        assert output_dir.exists()
        
        # Check product directories
        product_a_dir = output_dir / 'product_test_a'
        product_b_dir = output_dir / 'product_test_b'
        assert product_a_dir.exists()
        assert product_b_dir.exists()
        
        # Verify all aspect ratios generated for each product
        expected_ratios = ['1x1', '9x16', '16x9']
        for product_dir in [product_a_dir, product_b_dir]:
            for ratio in expected_ratios:
                # Find file with this ratio prefix
                files = list(product_dir.glob(f'{ratio}_*.png'))
                assert len(files) == 1, f"Expected 1 file for {ratio} in {product_dir}"
                
                # Verify file is valid image
                img = Image.open(files[0])
                assert img.size[0] > 0 and img.size[1] > 0
                
                # Verify aspect ratio is correct
                width, height = img.size
                actual_ratio = width / height
                
                if ratio == '1x1':
                    assert abs(actual_ratio - 1.0) < 0.01
                elif ratio == '9x16':
                    assert abs(actual_ratio - 9/16) < 0.01
                elif ratio == '16x9':
                    assert abs(actual_ratio - 16/9) < 0.01
    
    def test_e2e_with_asset_reuse(self, test_config, test_brief_yaml, temp_dirs):
        """
        Test end-to-end pipeline with existing input assets (reuse scenario).
        
        This test creates mock input assets and verifies they are reused
        instead of generating new ones.
        """
        # Create mock input assets
        input_dir = Path(temp_dirs['input'])
        
        # Create test images for both products
        for product_id in ['product_test_a', 'product_test_b']:
            img = Image.new('RGB', (1024, 1024), color='blue')
            img.save(input_dir / f'{product_id}.png')
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(test_config)
        
        # Run pipeline
        result = orchestrator.run(test_brief_yaml)
        
        # Verify execution success
        assert result.success, f"Pipeline failed: {result.errors}"
        
        # Verify outputs generated
        assert len(result.outputs) == 6
        
        # Verify all assets were reused (not generated)
        for asset in result.outputs:
            assert asset.was_generated is False, \
                f"Asset {asset.file_path} should have been reused"
        
        # Verify output files exist
        output_dir = Path(temp_dirs['output']) / 'test_campaign_e2e'
        assert output_dir.exists()
        
        # Verify all files are valid images
        for asset in result.outputs:
            assert Path(asset.file_path).exists()
            img = Image.open(asset.file_path)
            assert img.size[0] > 0 and img.size[1] > 0
    
    def test_e2e_text_overlay_applied(self, test_config, test_brief_yaml, temp_dirs):
        """
        Test that text overlay is properly applied to all outputs.
        
        This test uses mock input assets to avoid API calls.
        """
        # Create mock input assets
        input_dir = Path(temp_dirs['input'])
        
        # Create test images with distinct colors
        for product_id in ['product_test_a', 'product_test_b']:
            img = Image.new('RGB', (1024, 1024), color='red')
            img.save(input_dir / f'{product_id}.png')
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(test_config)
        
        # Run pipeline
        result = orchestrator.run(test_brief_yaml)
        
        # Verify execution success
        assert result.success
        
        # Load one of the output images and verify it's different from input
        # (text overlay should have modified the image)
        output_file = Path(result.outputs[0].file_path)
        output_img = Image.open(output_file)
        
        # Verify image dimensions are correct for aspect ratio
        assert output_img.size[0] > 0 and output_img.size[1] > 0
        
        # The image should not be pure red anymore (text overlay added)
        pixels = list(output_img.getdata())
        non_red_pixels = [p for p in pixels if p != (255, 0, 0)]
        assert len(non_red_pixels) > 0, "Text overlay should have modified the image"
    
    def test_e2e_mixed_scenario(self, test_config, test_brief_yaml, temp_dirs):
        """
        Test mixed scenario: one product with existing asset, one without.
        
        This test requires OPENAI_API_KEY for the product without an asset.
        """
        if not os.environ.get('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set - skipping real API test")
        
        # Create input asset for only one product
        input_dir = Path(temp_dirs['input'])
        img = Image.new('RGB', (1024, 1024), color='green')
        img.save(input_dir / 'product_test_a.png')
        
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(test_config)
        
        # Run pipeline
        result = orchestrator.run(test_brief_yaml)
        
        # Verify execution success
        assert result.success, f"Pipeline failed: {result.errors}"
        
        # Verify outputs
        assert len(result.outputs) == 6
        
        # Count reused vs generated
        reused = [a for a in result.outputs if not a.was_generated]
        generated = [a for a in result.outputs if a.was_generated]
        
        # Product A should be reused (3 variants)
        assert len(reused) == 3
        assert all('product_test_a' in a.file_path for a in reused)
        
        # Product B should be generated (3 variants)
        assert len(generated) == 3
        assert all('product_test_b' in a.file_path for a in generated)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

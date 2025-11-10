"""Integration tests for PipelineOrchestrator."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from src.orchestrator import PipelineOrchestrator
from src.models import CampaignBrief, Product, PipelineResult


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as input_dir, \
         tempfile.TemporaryDirectory() as output_dir:
        yield {
            'input_dir': input_dir,
            'output_dir': output_dir
        }


@pytest.fixture
def test_config(temp_dirs):
    """Create test configuration."""
    return {
        'storage': {
            'input_dir': temp_dirs['input_dir'],
            'output_dir': temp_dirs['output_dir']
        },
        'genai': {
            'provider': 'openai',
            'api_key': 'test-key',
            'model': 'dall-e-3'
        },
        'aspect_ratios': ['1:1', '9:16', '16:9'],
        'text_overlay': {
            'font_family': 'Arial',
            'font_size': 48,
            'color': '#FFFFFF',
            'position': 'bottom',
            'padding': 20,
            'background_opacity': 0.6
        },
        'logging': {
            'level': 'INFO',
            'file': None
        },
        'compliance': {
            'enabled': False
        }
    }


@pytest.fixture
def sample_brief_data():
    """Create sample campaign brief data."""
    return {
        'campaign_id': 'test_campaign_001',
        'products': [
            {
                'product_id': 'product_a',
                'name': 'Premium Coffee'
            },
            {
                'product_id': 'product_b',
                'name': 'Organic Tea'
            }
        ],
        'target_region': 'US',
        'target_audience': 'health-conscious millennials',
        'campaign_message': 'Start your day right'
    }


@pytest.fixture
def sample_brief_file(temp_dirs, sample_brief_data):
    """Create a sample brief file."""
    brief_path = Path(temp_dirs['input_dir']) / 'test_brief.json'
    with open(brief_path, 'w') as f:
        json.dump(sample_brief_data, f)
    return str(brief_path)


@pytest.fixture
def mock_image():
    """Create a mock PIL Image."""
    img = Image.new('RGB', (1024, 1024), color='blue')
    return img


def test_orchestrator_initialization(test_config):
    """Test that orchestrator initializes correctly with config."""
    orchestrator = PipelineOrchestrator(test_config)
    
    assert orchestrator.config == test_config
    assert orchestrator.asset_manager is not None
    assert orchestrator.compositor is not None
    assert orchestrator.logger is not None
    assert orchestrator.aspect_ratios == ['1:1', '9:16', '16:9']


def test_validate_brief_success(test_config, sample_brief_data):
    """Test brief validation with valid brief."""
    orchestrator = PipelineOrchestrator(test_config)
    
    brief = CampaignBrief(
        campaign_id=sample_brief_data['campaign_id'],
        products=[
            Product(
                product_id=p['product_id'],
                name=p['name']
            ) for p in sample_brief_data['products']
        ],
        target_region=sample_brief_data['target_region'],
        target_audience=sample_brief_data['target_audience'],
        campaign_message=sample_brief_data['campaign_message']
    )
    
    assert orchestrator._validate_brief(brief) is True


def test_validate_brief_failure_no_products(test_config):
    """Test brief validation fails with no products."""
    orchestrator = PipelineOrchestrator(test_config)
    
    brief = CampaignBrief(
        campaign_id='test_001',
        products=[],
        target_region='US',
        target_audience='millennials',
        campaign_message='Test message'
    )
    
    assert orchestrator._validate_brief(brief) is False


def test_end_to_end_with_generation(test_config, sample_brief_file, mock_image):
    """Test end-to-end pipeline with GenAI generation."""
    # Setup mock GenAI client
    mock_client = Mock()
    mock_client._build_prompt = Mock(return_value="test prompt")
    mock_client.generate_image = Mock(return_value=mock_image)
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(test_config)
    orchestrator.genai_client = mock_client
    
    # Run pipeline
    result = orchestrator.run(sample_brief_file)
    
    # Verify result
    assert isinstance(result, PipelineResult)
    assert result.campaign_id == 'test_campaign_001'
    assert result.success is True
    assert len(result.outputs) == 6  # 2 products × 3 aspect ratios
    assert len(result.errors) == 0
    
    # Verify all assets were generated (not reused)
    for asset in result.outputs:
        assert asset.was_generated is True
    
    # Verify GenAI was called for each product
    assert mock_client.generate_image.call_count == 2


def test_end_to_end_with_asset_reuse(test_config, sample_brief_file, mock_image, temp_dirs):
    """Test end-to-end pipeline with existing assets."""
    # Create existing input assets
    input_dir = Path(temp_dirs['input_dir'])
    for product_id in ['product_a', 'product_b']:
        asset_path = input_dir / f'{product_id}.png'
        mock_image.save(asset_path)
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(test_config)
    
    # Mock GenAI client (should not be called)
    mock_client = Mock()
    orchestrator.genai_client = mock_client
    
    # Run pipeline
    result = orchestrator.run(sample_brief_file)
    
    # Verify result
    assert isinstance(result, PipelineResult)
    assert result.success is True
    assert len(result.outputs) == 6  # 2 products × 3 aspect ratios
    
    # Verify all assets were reused (not generated)
    for asset in result.outputs:
        assert asset.was_generated is False
    
    # Verify GenAI was NOT called
    mock_client.generate_image.assert_not_called()


def test_error_handling_single_product_failure(test_config, sample_brief_file, mock_image):
    """Test that pipeline continues when one product fails."""
    # Setup mock GenAI client that fails for first product
    mock_client = Mock()
    mock_client._build_prompt = Mock(return_value="test prompt")
    
    # First call fails, second succeeds
    mock_client.generate_image = Mock(side_effect=[
        Exception("Generation failed"),
        mock_image
    ])
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(test_config)
    orchestrator.genai_client = mock_client
    
    # Run pipeline
    result = orchestrator.run(sample_brief_file)
    
    # Verify result
    assert isinstance(result, PipelineResult)
    assert result.success is False  # Overall failure due to errors
    assert len(result.errors) == 1  # One product failed
    assert len(result.outputs) == 3  # Only second product succeeded (3 aspect ratios)
    
    # Verify error message contains product ID
    assert 'product_a' in result.errors[0]


def test_error_handling_invalid_brief(test_config, temp_dirs):
    """Test error handling with invalid brief file."""
    # Create invalid brief file
    brief_path = Path(temp_dirs['input_dir']) / 'invalid_brief.json'
    with open(brief_path, 'w') as f:
        f.write('{ invalid json }')
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(test_config)
    
    # Run pipeline
    result = orchestrator.run(str(brief_path))
    
    # Verify result
    assert isinstance(result, PipelineResult)
    assert result.success is False
    assert len(result.errors) > 0


def test_error_handling_missing_brief(test_config):
    """Test error handling with missing brief file."""
    orchestrator = PipelineOrchestrator(test_config)
    
    # Run pipeline with non-existent file
    result = orchestrator.run('/nonexistent/brief.json')
    
    # Verify result
    assert isinstance(result, PipelineResult)
    assert result.success is False
    assert len(result.errors) > 0


def test_multiple_products_processing(test_config, temp_dirs, mock_image):
    """Test processing multiple products in a single campaign."""
    # Create brief with 3 products
    brief_data = {
        'campaign_id': 'multi_product_campaign',
        'products': [
            {'product_id': f'product_{i}', 'name': f'Product {i}'}
            for i in range(3)
        ],
        'target_region': 'US',
        'target_audience': 'everyone',
        'campaign_message': 'Buy now'
    }
    
    brief_path = Path(temp_dirs['input_dir']) / 'multi_brief.json'
    with open(brief_path, 'w') as f:
        json.dump(brief_data, f)
    
    # Setup mock GenAI client
    mock_client = Mock()
    mock_client._build_prompt = Mock(return_value="test prompt")
    mock_client.generate_image = Mock(return_value=mock_image)
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(test_config)
    orchestrator.genai_client = mock_client
    
    # Run pipeline
    result = orchestrator.run(str(brief_path))
    
    # Verify result
    assert result.success is True
    assert len(result.outputs) == 9  # 3 products × 3 aspect ratios
    
    # Verify all products were processed
    product_ids = set(asset.product_id for asset in result.outputs)
    assert product_ids == {'product_0', 'product_1', 'product_2'}
    
    # Verify GenAI was called for each product
    assert mock_client.generate_image.call_count == 3


def test_report_generation(test_config, sample_brief_file, mock_image, temp_dirs):
    """Test that execution report is generated."""
    # Create existing input assets
    input_dir = Path(temp_dirs['input_dir'])
    for product_id in ['product_a', 'product_b']:
        asset_path = input_dir / f'{product_id}.png'
        mock_image.save(asset_path)
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator(test_config)
    
    # Run pipeline
    result = orchestrator.run(sample_brief_file)
    
    # Verify report file was created
    report_path = Path(temp_dirs['output_dir']) / 'test_campaign_001' / 'report.json'
    assert report_path.exists()
    
    # Verify report content
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report['campaign_id'] == 'test_campaign_001'
    assert report['success'] is True
    assert report['summary']['products_processed'] == 2
    assert report['summary']['total_assets'] == 6
    assert report['summary']['assets_reused'] == 6
    assert report['summary']['assets_generated'] == 0

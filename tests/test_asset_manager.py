"""Unit tests for AssetManager."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from PIL import Image

from src.managers.asset_manager import AssetManager


class TestAssetManager:
    """Test suite for AssetManager class."""

    @pytest.fixture
    def temp_dirs(self):
        """Fixture providing temporary input and output directories."""
        with TemporaryDirectory() as input_dir, TemporaryDirectory() as output_dir:
            yield input_dir, output_dir

    @pytest.fixture
    def asset_manager(self, temp_dirs):
        """Fixture providing an AssetManager instance."""
        input_dir, output_dir = temp_dirs
        return AssetManager(input_dir, output_dir)

    @pytest.fixture
    def sample_image(self):
        """Fixture providing a sample PIL Image."""
        # Create a simple 100x100 red image
        image = Image.new('RGB', (100, 100), color='red')
        return image

    def test_init_creates_directories(self, temp_dirs):
        """Test that initialization creates input and output directories."""
        input_dir, output_dir = temp_dirs
        
        # Remove directories to test creation
        Path(input_dir).rmdir()
        Path(output_dir).rmdir()
        
        manager = AssetManager(input_dir, output_dir)
        
        assert Path(input_dir).exists()
        assert Path(output_dir).exists()

    def test_get_asset_existing_png(self, asset_manager, temp_dirs, sample_image):
        """Test retrieving an existing PNG asset."""
        input_dir, _ = temp_dirs
        
        # Save a test image
        test_path = Path(input_dir) / 'product_a.png'
        sample_image.save(test_path)
        
        # Retrieve the asset
        retrieved = asset_manager.get_asset('product_a')
        
        assert retrieved is not None
        assert isinstance(retrieved, Image.Image)
        assert retrieved.size == (100, 100)

    def test_get_asset_existing_jpg(self, asset_manager, temp_dirs, sample_image):
        """Test retrieving an existing JPG asset."""
        input_dir, _ = temp_dirs
        
        # Save a test image as JPG
        test_path = Path(input_dir) / 'product_b.jpg'
        sample_image.save(test_path)
        
        # Retrieve the asset
        retrieved = asset_manager.get_asset('product_b')
        
        assert retrieved is not None
        assert isinstance(retrieved, Image.Image)

    def test_get_asset_existing_jpeg(self, asset_manager, temp_dirs, sample_image):
        """Test retrieving an existing JPEG asset."""
        input_dir, _ = temp_dirs
        
        # Save a test image as JPEG
        test_path = Path(input_dir) / 'product_c.jpeg'
        sample_image.save(test_path)
        
        # Retrieve the asset
        retrieved = asset_manager.get_asset('product_c')
        
        assert retrieved is not None
        assert isinstance(retrieved, Image.Image)

    def test_get_asset_missing(self, asset_manager):
        """Test retrieving a non-existent asset returns None."""
        retrieved = asset_manager.get_asset('nonexistent_product')
        
        assert retrieved is None

    def test_save_asset_creates_directory_structure(self, asset_manager, temp_dirs, sample_image):
        """Test that save_asset creates the proper directory structure."""
        _, output_dir = temp_dirs
        
        file_path = asset_manager.save_asset(
            campaign_id='campaign_001',
            product_id='product_a',
            aspect_ratio='1x1',
            image=sample_image
        )
        
        # Check directory structure
        expected_dir = Path(output_dir) / 'campaign_001' / 'product_a'
        assert expected_dir.exists()
        assert expected_dir.is_dir()
        
        # Check file exists
        assert Path(file_path).exists()
        assert Path(file_path).is_file()

    def test_save_asset_filename_format(self, asset_manager, temp_dirs, sample_image):
        """Test that save_asset generates correct filename format."""
        _, output_dir = temp_dirs
        
        file_path = asset_manager.save_asset(
            campaign_id='campaign_001',
            product_id='product_a',
            aspect_ratio='1x1',
            image=sample_image
        )
        
        # Check filename format
        filename = Path(file_path).name
        assert filename == '1x1_product_a.png'

    def test_save_asset_multiple_aspect_ratios(self, asset_manager, temp_dirs, sample_image):
        """Test saving multiple aspect ratios for the same product."""
        _, output_dir = temp_dirs
        
        aspect_ratios = ['1x1', '9x16', '16x9']
        saved_paths = []
        
        for ratio in aspect_ratios:
            file_path = asset_manager.save_asset(
                campaign_id='campaign_001',
                product_id='product_a',
                aspect_ratio=ratio,
                image=sample_image
            )
            saved_paths.append(file_path)
        
        # Verify all files exist
        for path in saved_paths:
            assert Path(path).exists()
        
        # Verify correct filenames
        filenames = [Path(p).name for p in saved_paths]
        assert '1x1_product_a.png' in filenames
        assert '9x16_product_a.png' in filenames
        assert '16x9_product_a.png' in filenames

    def test_save_asset_preserves_image_quality(self, asset_manager, temp_dirs, sample_image):
        """Test that saved images maintain quality."""
        file_path = asset_manager.save_asset(
            campaign_id='campaign_001',
            product_id='product_a',
            aspect_ratio='1x1',
            image=sample_image
        )
        
        # Load saved image and verify
        loaded_image = Image.open(file_path)
        assert loaded_image.size == sample_image.size
        assert loaded_image.mode == sample_image.mode

    def test_organize_outputs_empty_campaign(self, asset_manager):
        """Test organize_outputs with non-existent campaign."""
        outputs = asset_manager.organize_outputs('nonexistent_campaign')
        
        assert outputs == {}

    def test_organize_outputs_single_product(self, asset_manager, temp_dirs, sample_image):
        """Test organize_outputs with a single product."""
        # Save some assets
        asset_manager.save_asset('campaign_001', 'product_a', '1x1', sample_image)
        asset_manager.save_asset('campaign_001', 'product_a', '9x16', sample_image)
        
        outputs = asset_manager.organize_outputs('campaign_001')
        
        assert 'product_a' in outputs
        assert len(outputs['product_a']) == 2
        assert any('1x1_product_a.png' in path for path in outputs['product_a'])
        assert any('9x16_product_a.png' in path for path in outputs['product_a'])

    def test_organize_outputs_multiple_products(self, asset_manager, temp_dirs, sample_image):
        """Test organize_outputs with multiple products."""
        # Save assets for multiple products
        asset_manager.save_asset('campaign_001', 'product_a', '1x1', sample_image)
        asset_manager.save_asset('campaign_001', 'product_b', '1x1', sample_image)
        asset_manager.save_asset('campaign_001', 'product_b', '16x9', sample_image)
        
        outputs = asset_manager.organize_outputs('campaign_001')
        
        assert 'product_a' in outputs
        assert 'product_b' in outputs
        assert len(outputs['product_a']) == 1
        assert len(outputs['product_b']) == 2

    def test_organize_outputs_sorted(self, asset_manager, temp_dirs, sample_image):
        """Test that organize_outputs returns sorted file paths."""
        # Save assets in non-alphabetical order
        asset_manager.save_asset('campaign_001', 'product_a', '9x16', sample_image)
        asset_manager.save_asset('campaign_001', 'product_a', '16x9', sample_image)
        asset_manager.save_asset('campaign_001', 'product_a', '1x1', sample_image)
        
        outputs = asset_manager.organize_outputs('campaign_001')
        
        # Verify files are sorted
        files = outputs['product_a']
        assert files == sorted(files)

    def test_generate_filename_standard_format(self, asset_manager):
        """Test filename generation with standard aspect ratios."""
        filename = asset_manager._generate_filename('product_a', '1x1')
        assert filename == '1x1_product_a.png'
        
        filename = asset_manager._generate_filename('product_b', '9x16')
        assert filename == '9x16_product_b.png'

    def test_generate_filename_colon_format(self, asset_manager):
        """Test filename generation handles colon format aspect ratios."""
        filename = asset_manager._generate_filename('product_a', '1:1')
        assert filename == '1x1_product_a.png'
        
        filename = asset_manager._generate_filename('product_b', '16:9')
        assert filename == '16x9_product_b.png'

    def test_generate_filename_case_normalization(self, asset_manager):
        """Test filename generation normalizes case."""
        filename = asset_manager._generate_filename('product_a', '1X1')
        assert filename == '1x1_product_a.png'

"""Unit tests for BriefParser."""

import json
import yaml
import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile

from src.parsers.brief_parser import BriefParser
from src.models import CampaignBrief


class TestBriefParser:
    """Test suite for BriefParser class."""

    @pytest.fixture
    def valid_brief_data(self):
        """Fixture providing valid brief data."""
        return {
            'campaign_id': 'campaign_001',
            'products': [
                {
                    'product_id': 'product_a',
                    'name': 'Premium Coffee',
                    'description': 'High-quality organic coffee'
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
    def valid_brief_with_localization(self, valid_brief_data):
        """Fixture providing valid brief data with localization."""
        data = valid_brief_data.copy()
        data['localization'] = {
            'language': 'en',
            'region_specific_message': 'Good morning America'
        }
        return data

    def test_parse_valid_json(self, valid_brief_data):
        """Test parsing a valid JSON brief file."""
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_brief_data, f)
            temp_path = f.name

        try:
            brief = BriefParser.parse(temp_path)
            
            assert isinstance(brief, CampaignBrief)
            assert brief.campaign_id == 'campaign_001'
            assert len(brief.products) == 2
            assert brief.products[0].product_id == 'product_a'
            assert brief.products[0].name == 'Premium Coffee'
            assert brief.products[1].product_id == 'product_b'
            assert brief.target_region == 'US'
            assert brief.target_audience == 'health-conscious millennials'
            assert brief.campaign_message == 'Start your day right'
            assert brief.localization is None
        finally:
            Path(temp_path).unlink()

    def test_parse_valid_yaml(self, valid_brief_data):
        """Test parsing a valid YAML brief file."""
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_brief_data, f)
            temp_path = f.name

        try:
            brief = BriefParser.parse(temp_path)
            
            assert isinstance(brief, CampaignBrief)
            assert brief.campaign_id == 'campaign_001'
            assert len(brief.products) == 2
            assert brief.target_region == 'US'
        finally:
            Path(temp_path).unlink()

    def test_parse_valid_yml_extension(self, valid_brief_data):
        """Test parsing a YAML file with .yml extension."""
        with NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(valid_brief_data, f)
            temp_path = f.name

        try:
            brief = BriefParser.parse(temp_path)
            assert isinstance(brief, CampaignBrief)
        finally:
            Path(temp_path).unlink()

    def test_parse_with_localization(self, valid_brief_with_localization):
        """Test parsing a brief with localization data."""
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_brief_with_localization, f)
            temp_path = f.name

        try:
            brief = BriefParser.parse(temp_path)
            
            assert brief.localization is not None
            assert brief.localization.language == 'en'
            assert brief.localization.region_specific_message == 'Good morning America'
        finally:
            Path(temp_path).unlink()

    def test_parse_missing_campaign_id(self, valid_brief_data):
        """Test parsing fails when campaign_id is missing."""
        data = valid_brief_data.copy()
        del data['campaign_id']
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing required fields.*campaign_id"):
                BriefParser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_missing_products(self, valid_brief_data):
        """Test parsing fails when products are missing."""
        data = valid_brief_data.copy()
        del data['products']
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing required fields.*products"):
                BriefParser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_empty_products(self, valid_brief_data):
        """Test parsing fails when products list is empty."""
        data = valid_brief_data.copy()
        data['products'] = []
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="At least one product is required"):
                BriefParser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_missing_target_region(self, valid_brief_data):
        """Test parsing fails when target_region is missing."""
        data = valid_brief_data.copy()
        del data['target_region']
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Missing required fields.*target_region"):
                BriefParser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_product_missing_id(self, valid_brief_data):
        """Test parsing fails when a product is missing product_id."""
        data = valid_brief_data.copy()
        data['products'][0] = {'name': 'Coffee'}  # Missing product_id
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Product at index 0 missing 'product_id'"):
                BriefParser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_product_missing_name(self, valid_brief_data):
        """Test parsing fails when a product is missing name."""
        data = valid_brief_data.copy()
        data['products'][0] = {'product_id': 'product_a'}  # Missing name
        
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Product at index 0 missing 'name'"):
                BriefParser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_malformed_json(self):
        """Test parsing fails with malformed JSON."""
        with NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json content}')
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON format"):
                BriefParser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_malformed_yaml(self):
        """Test parsing fails with malformed YAML."""
        with NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('invalid:\n  - yaml: content:\n    - broken')
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML format"):
                BriefParser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_parse_file_not_found(self):
        """Test parsing fails when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Brief file not found"):
            BriefParser.parse('/nonexistent/path/brief.json')

    def test_parse_unsupported_extension(self, valid_brief_data):
        """Test parsing fails with unsupported file extension."""
        with NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            json.dump(valid_brief_data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported file extension"):
                BriefParser.parse(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_detect_format_json(self):
        """Test format detection for JSON files."""
        assert BriefParser._detect_format('brief.json') == 'json'

    def test_detect_format_yaml(self):
        """Test format detection for YAML files."""
        assert BriefParser._detect_format('brief.yaml') == 'yaml'
        assert BriefParser._detect_format('brief.yml') == 'yaml'

    def test_detect_format_case_insensitive(self):
        """Test format detection is case insensitive."""
        assert BriefParser._detect_format('brief.JSON') == 'json'
        assert BriefParser._detect_format('brief.YAML') == 'yaml'

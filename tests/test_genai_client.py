"""Integration tests for GenAI clients with mocked API."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from io import BytesIO
import openai

from src.clients.openai_client import OpenAIClient


class TestOpenAIClient:
    """Test suite for OpenAIClient class."""

    @pytest.fixture
    def api_key(self):
        """Fixture providing a test API key."""
        return "test-api-key-12345"

    @pytest.fixture
    def client(self, api_key):
        """Fixture providing an OpenAIClient instance."""
        return OpenAIClient(api_key=api_key)

    @pytest.fixture
    def sample_image(self):
        """Fixture providing a sample PIL Image."""
        image = Image.new('RGB', (1024, 1024), color='blue')
        return image

    @pytest.fixture
    def mock_image_response(self, sample_image):
        """Fixture providing a mock image response as bytes."""
        buffer = BytesIO()
        sample_image.save(buffer, format='PNG')
        return buffer.getvalue()

    def test_init_sets_api_key(self, api_key):
        """Test that initialization sets the API key correctly."""
        client = OpenAIClient(api_key=api_key)
        assert client.api_key == api_key
        assert client.model == "dall-e-3"

    def test_init_custom_model(self, api_key):
        """Test initialization with custom model."""
        client = OpenAIClient(api_key=api_key, model="dall-e-2")
        assert client.model == "dall-e-2"

    def test_build_prompt(self, client):
        """Test prompt construction with product, audience, and region context."""
        prompt = client._build_prompt(
            product_name="Premium Coffee",
            audience="health-conscious millennials",
            region="US"
        )
        
        assert "Premium Coffee" in prompt
        assert "health-conscious millennials" in prompt
        assert "US" in prompt
        assert "advertising" in prompt.lower()
        assert "professional" in prompt.lower()

    def test_format_size_square(self, client):
        """Test size formatting for square images."""
        size_str = client._format_size((1024, 1024))
        assert size_str == "1024x1024"

    def test_format_size_vertical(self, client):
        """Test size formatting for vertical images."""
        size_str = client._format_size((1024, 1792))
        assert size_str == "1024x1792"

    def test_format_size_horizontal(self, client):
        """Test size formatting for horizontal images."""
        size_str = client._format_size((1792, 1024))
        assert size_str == "1792x1024"

    def test_calculate_backoff(self, client):
        """Test exponential backoff calculation."""
        assert client._calculate_backoff(0) == 2  # 2 * 2^0
        assert client._calculate_backoff(1) == 4  # 2 * 2^1
        assert client._calculate_backoff(2) == 8  # 2 * 2^2

    @patch('src.clients.openai_client.requests.get')
    def test_download_image_success(self, mock_get, client, mock_image_response):
        """Test successful image download and conversion."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.content = mock_image_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        image = client._download_image("https://example.com/image.png")
        
        assert isinstance(image, Image.Image)
        assert image.mode == 'RGB'
        assert image.size == (1024, 1024)

    @patch('src.clients.openai_client.requests.get')
    def test_download_image_network_error(self, mock_get, client):
        """Test image download handles network errors."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        with pytest.raises(Exception, match="Failed to download image"):
            client._download_image("https://example.com/image.png")

    @patch('src.clients.openai_client.requests.get')
    @patch.object(OpenAIClient, '_download_image')
    def test_generate_image_success(self, mock_download, mock_get, client, sample_image):
        """Test successful image generation."""
        # Mock OpenAI API response
        mock_response = MagicMock()
        mock_response.data = [MagicMock(url="https://example.com/generated.png")]
        
        with patch.object(client.client.images, 'generate', return_value=mock_response):
            mock_download.return_value = sample_image
            
            result = client.generate_image("A beautiful landscape", size=(1024, 1024))
            
            assert isinstance(result, Image.Image)
            assert result.size == (1024, 1024)

    @patch.object(OpenAIClient, '_download_image')
    def test_generate_image_with_retry_on_rate_limit(self, mock_download, client, sample_image):
        """Test that generation retries on rate limit errors."""
        mock_download.return_value = sample_image
        
        # Mock API to fail twice then succeed
        mock_response = MagicMock()
        mock_response.data = [MagicMock(url="https://example.com/generated.png")]
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise openai.RateLimitError("Rate limit exceeded", response=Mock(), body=None)
            return mock_response
        
        with patch.object(client.client.images, 'generate', side_effect=side_effect):
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = client.generate_image("Test prompt")
                
                assert isinstance(result, Image.Image)
                assert call_count == 3  # Failed twice, succeeded on third

    @patch.object(OpenAIClient, '_download_image')
    def test_generate_image_fails_after_max_retries(self, mock_download, client):
        """Test that generation fails after max retries."""
        # Mock API to always fail
        with patch.object(client.client.images, 'generate', 
                         side_effect=openai.RateLimitError("Rate limit", response=Mock(), body=None)):
            with patch('time.sleep'):  # Mock sleep to speed up test
                with pytest.raises(Exception, match="Rate limit exceeded after 3 attempts"):
                    client.generate_image("Test prompt")

    @patch.object(OpenAIClient, '_download_image')
    def test_generate_image_handles_api_error(self, mock_download, client, sample_image):
        """Test handling of API errors with retry."""
        mock_download.return_value = sample_image
        
        # Mock API to fail once then succeed
        mock_response = MagicMock()
        mock_response.data = [MagicMock(url="https://example.com/generated.png")]
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise openai.APIError("API error", request=Mock(), body=None)
            return mock_response
        
        with patch.object(client.client.images, 'generate', side_effect=side_effect):
            with patch('time.sleep'):
                result = client.generate_image("Test prompt")
                
                assert isinstance(result, Image.Image)
                assert call_count == 2

    @patch.object(OpenAIClient, '_download_image')
    def test_generate_image_handles_connection_error(self, mock_download, client, sample_image):
        """Test handling of connection errors with retry."""
        mock_download.return_value = sample_image
        
        # Mock API to fail with connection error then succeed
        mock_response = MagicMock()
        mock_response.data = [MagicMock(url="https://example.com/generated.png")]
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise openai.APIConnectionError(request=Mock())
            return mock_response
        
        with patch.object(client.client.images, 'generate', side_effect=side_effect):
            with patch('time.sleep'):
                result = client.generate_image("Test prompt")
                
                assert isinstance(result, Image.Image)
                assert call_count == 2

    def test_generate_image_handles_unexpected_error(self, client):
        """Test that unexpected errors are raised without retry."""
        with patch.object(client.client.images, 'generate', 
                         side_effect=ValueError("Unexpected error")):
            with pytest.raises(Exception, match="Unexpected error during image generation"):
                client.generate_image("Test prompt")

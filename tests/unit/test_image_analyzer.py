"""
Tests for the image analyzer module.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from openhands.vision.image_analyzer import ImageAnalyzer, AnalysisType, ImageAnalysisResult


@pytest.fixture
def test_image_path():
    """Create a simple test image."""
    from PIL import Image
    
    # Create a temporary directory for test images
    temp_dir = Path("/tmp/openhands_test_images")
    temp_dir.mkdir(exist_ok=True)
    
    # Create a simple test image
    img_path = temp_dir / "test_image.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_path)
    
    yield img_path
    
    # Clean up
    if img_path.exists():
        os.unlink(img_path)


@pytest.mark.asyncio
async def test_basic_image_analysis(test_image_path):
    """Test basic image analysis without an LLM."""
    analyzer = ImageAnalyzer()
    
    # Test describe analysis
    result = await analyzer.analyze(test_image_path, AnalysisType.DESCRIBE)
    
    assert isinstance(result, ImageAnalysisResult)
    assert result.analysis_type == AnalysisType.DESCRIBE
    assert "100x100 pixels" in result.content
    assert "RGB" in result.content
    
    # Check metadata
    assert result.metadata["width"] == 100
    assert result.metadata["height"] == 100
    assert result.metadata["mode"] == "RGB"


@pytest.mark.asyncio
async def test_analyze_with_llm(test_image_path):
    """Test image analysis with a mock LLM."""
    # Create a mock LLM
    mock_llm = AsyncMock()
    mock_llm.analyze_image = AsyncMock(return_value="This is a red square image.")
    mock_llm.config = MagicMock()
    mock_llm.config.model = "test-model"
    
    analyzer = ImageAnalyzer(mock_llm)
    
    # Test with the mock LLM
    result = await analyzer.analyze(test_image_path, AnalysisType.DESCRIBE)
    
    assert isinstance(result, ImageAnalysisResult)
    assert result.analysis_type == AnalysisType.DESCRIBE
    assert result.content == "This is a red square image."
    assert result.metadata["model"] == "test-model"
    
    # Verify the LLM was called with the correct arguments
    mock_llm.analyze_image.assert_called_once()
    # The first argument should be the base64 image
    assert isinstance(mock_llm.analyze_image.call_args[0][0], str)
    # The second argument should be the prompt
    assert "Describe this image" in mock_llm.analyze_image.call_args[0][1]


@pytest.mark.asyncio
async def test_analyze_from_bytes(test_image_path):
    """Test analyzing an image from bytes."""
    # Read the test image into bytes
    with open(test_image_path, "rb") as f:
        image_bytes = f.read()
    
    analyzer = ImageAnalyzer()
    
    # Test analyze_from_bytes
    result = await analyzer.analyze_from_bytes(
        image_bytes, AnalysisType.DESCRIBE, filename="test_from_bytes.png"
    )
    
    assert isinstance(result, ImageAnalysisResult)
    assert result.analysis_type == AnalysisType.DESCRIBE
    assert "100x100 pixels" in result.content
    assert "RGB" in result.content


@pytest.mark.asyncio
async def test_invalid_image_path():
    """Test handling of invalid image paths."""
    analyzer = ImageAnalyzer()
    
    # Test with a non-existent image
    with pytest.raises(FileNotFoundError):
        await analyzer.analyze("/path/to/nonexistent/image.png")


@pytest.mark.asyncio
async def test_different_analysis_types(test_image_path):
    """Test different analysis types."""
    analyzer = ImageAnalyzer()
    
    # Test all analysis types
    for analysis_type in AnalysisType:
        result = await analyzer.analyze(test_image_path, analysis_type)
        assert result.analysis_type == analysis_type
        assert isinstance(result.content, str)
        assert len(result.content) > 0
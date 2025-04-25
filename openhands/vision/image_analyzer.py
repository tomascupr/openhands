"""
Image analyzer module for processing and analyzing images.
"""
import base64
import io
import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from PIL import Image

from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM


class AnalysisType(str, Enum):
    """Types of image analysis that can be performed."""
    
    DESCRIBE = "describe"
    """Generate a detailed description of the image."""
    
    OCR = "ocr"
    """Extract text from the image."""
    
    CODE = "code"
    """Extract and analyze code from the image."""
    
    UI = "ui"
    """Analyze UI elements in the image."""
    
    DIAGRAM = "diagram"
    """Analyze diagrams, flowcharts, or other visual representations."""


class ImageAnalysisResult:
    """Result of image analysis."""
    
    def __init__(
        self,
        analysis_type: AnalysisType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an image analysis result.
        
        Args:
            analysis_type: The type of analysis performed
            content: The main content of the analysis (text description, extracted text, etc.)
            metadata: Additional metadata about the analysis
        """
        self.analysis_type = analysis_type
        self.content = content
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "analysis_type": self.analysis_type,
            "content": self.content,
            "metadata": self.metadata,
        }


class ImageAnalyzer:
    """
    Analyzer for processing and extracting information from images.
    
    This class provides methods for analyzing images using various techniques,
    including using vision-capable LLMs for image understanding.
    """
    
    def __init__(self, llm: Optional[LLM] = None):
        """
        Initialize the image analyzer.
        
        Args:
            llm: Language model with vision capabilities
        """
        self.llm = llm
    
    async def analyze(
        self,
        image_path: Union[str, Path],
        analysis_type: AnalysisType = AnalysisType.DESCRIBE,
        prompt: Optional[str] = None,
    ) -> ImageAnalysisResult:
        """
        Analyze an image.
        
        Args:
            image_path: Path to the image file
            analysis_type: Type of analysis to perform
            prompt: Optional prompt to guide the analysis
            
        Returns:
            An ImageAnalysisResult containing the analysis
        """
        # Ensure the image exists
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Prepare the image
        try:
            image = Image.open(image_path)
            # Resize very large images to reduce processing time
            if max(image.size) > 2000:
                image.thumbnail((2000, 2000), Image.LANCZOS)
        except Exception as e:
            logger.error(f"Error opening image: {e}")
            raise ValueError(f"Invalid image file: {e}")
        
        # Perform the analysis based on the type
        if self.llm and hasattr(self.llm, "analyze_image"):
            # Use the LLM for image analysis if available
            return await self._analyze_with_llm(image, analysis_type, prompt)
        else:
            # Fall back to basic analysis
            return await self._analyze_basic(image, analysis_type)
    
    async def analyze_from_bytes(
        self,
        image_bytes: bytes,
        analysis_type: AnalysisType = AnalysisType.DESCRIBE,
        prompt: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> ImageAnalysisResult:
        """
        Analyze an image from bytes.
        
        Args:
            image_bytes: Raw image data
            analysis_type: Type of analysis to perform
            prompt: Optional prompt to guide the analysis
            filename: Optional filename for the image
            
        Returns:
            An ImageAnalysisResult containing the analysis
        """
        # Create a temporary file to store the image
        temp_dir = Path("/tmp/openhands_images")
        temp_dir.mkdir(exist_ok=True)
        
        if filename:
            # Use the provided filename but ensure it's safe
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
            temp_path = temp_dir / safe_filename
        else:
            # Generate a random filename
            import uuid
            temp_path = temp_dir / f"image_{uuid.uuid4()}.png"
        
        # Write the image to the temporary file
        with open(temp_path, "wb") as f:
            f.write(image_bytes)
        
        try:
            # Analyze the image
            result = await self.analyze(temp_path, analysis_type, prompt)
            return result
        finally:
            # Clean up the temporary file
            if temp_path.exists():
                os.unlink(temp_path)
    
    async def _analyze_with_llm(
        self,
        image: Image.Image,
        analysis_type: AnalysisType,
        prompt: Optional[str] = None,
    ) -> ImageAnalysisResult:
        """
        Analyze an image using a vision-capable LLM.
        
        Args:
            image: The image to analyze
            analysis_type: Type of analysis to perform
            prompt: Optional prompt to guide the analysis
            
        Returns:
            An ImageAnalysisResult containing the analysis
        """
        if not self.llm:
            raise ValueError("No LLM provided for image analysis")
        
        # Convert the image to base64
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Create a prompt based on the analysis type
        if not prompt:
            prompt = self._get_default_prompt(analysis_type)
        
        # Call the LLM's image analysis method
        try:
            response = await self.llm.analyze_image(img_str, prompt)
            return ImageAnalysisResult(
                analysis_type=analysis_type,
                content=response,
                metadata={"model": self.llm.config.model},
            )
        except Exception as e:
            logger.error(f"Error analyzing image with LLM: {e}")
            return ImageAnalysisResult(
                analysis_type=analysis_type,
                content=f"Error analyzing image: {e}",
                metadata={"error": str(e)},
            )
    
    async def _analyze_basic(
        self, image: Image.Image, analysis_type: AnalysisType
    ) -> ImageAnalysisResult:
        """
        Perform basic image analysis without an LLM.
        
        Args:
            image: The image to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            An ImageAnalysisResult containing the analysis
        """
        # Extract basic image information
        width, height = image.size
        format_name = image.format or "Unknown"
        mode = image.mode
        
        # Create a basic description
        content = f"Image: {width}x{height} pixels, {format_name} format, {mode} mode"
        
        # Add more information based on the analysis type
        if analysis_type == AnalysisType.DESCRIBE:
            # Add basic color information
            if mode == "RGB":
                try:
                    # Get the dominant colors
                    colors = image.getcolors(maxcolors=10000)
                    if colors:
                        # Sort by frequency (descending)
                        colors.sort(reverse=True, key=lambda x: x[0])
                        # Take the top 5 colors
                        top_colors = colors[:5]
                        color_info = "\nDominant colors (RGB):\n"
                        for count, color in top_colors:
                            color_info += f"- {color}: {count} pixels\n"
                        content += color_info
                except Exception as e:
                    logger.warning(f"Error getting color information: {e}")
        
        return ImageAnalysisResult(
            analysis_type=analysis_type,
            content=content,
            metadata={
                "width": width,
                "height": height,
                "format": format_name,
                "mode": mode,
            },
        )
    
    def _get_default_prompt(self, analysis_type: AnalysisType) -> str:
        """
        Get a default prompt for the given analysis type.
        
        Args:
            analysis_type: The type of analysis to perform
            
        Returns:
            A prompt string
        """
        prompts = {
            AnalysisType.DESCRIBE: (
                "Describe this image in detail. Include information about the main "
                "subjects, colors, composition, and any text visible in the image."
            ),
            AnalysisType.OCR: (
                "Extract all text visible in this image. Maintain the original "
                "formatting as much as possible."
            ),
            AnalysisType.CODE: (
                "Extract and analyze the code shown in this image. Identify the "
                "programming language, explain what the code does, and note any "
                "potential issues or bugs."
            ),
            AnalysisType.UI: (
                "Analyze the user interface shown in this image. Identify UI elements "
                "like buttons, text fields, menus, etc. Describe the layout and "
                "potential functionality."
            ),
            AnalysisType.DIAGRAM: (
                "Analyze the diagram or chart in this image. Describe its type, "
                "components, relationships, and the information it conveys."
            ),
        }
        
        return prompts.get(
            analysis_type,
            "Describe this image and provide any relevant information.",
        )
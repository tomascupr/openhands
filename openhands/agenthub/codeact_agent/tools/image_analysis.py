"""
Tool for analyzing images.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from openhands.core.logger import openhands_logger as logger
from openhands.vision.image_analyzer import AnalysisType, ImageAnalyzer


def create_image_analysis_tool(llm=None):
    """
    Create a tool for analyzing images.
    
    Args:
        llm: Language model with vision capabilities
        
    Returns:
        A dictionary describing the tool
    """
    analyzer = ImageAnalyzer(llm)
    
    async def image_analysis_tool(
        image_path: str,
        analysis_type: str = "describe",
        prompt: Optional[str] = None,
    ) -> str:
        """
        Analyze an image.
        
        Args:
            image_path: Path to the image file
            analysis_type: Type of analysis to perform (describe, ocr, code, ui, diagram)
            prompt: Optional prompt to guide the analysis
            
        Returns:
            A string containing the analysis results
        """
        # Validate the image path
        if not os.path.exists(image_path):
            return f"Error: Image file not found at {image_path}"
        
        # Validate the analysis type
        try:
            analysis_type_enum = AnalysisType(analysis_type.lower())
        except ValueError:
            valid_types = ", ".join([t.value for t in AnalysisType])
            return f"Error: Invalid analysis type '{analysis_type}'. Valid types are: {valid_types}"
        
        try:
            # Perform the analysis
            result = await analyzer.analyze(
                image_path, analysis_type_enum, prompt
            )
            
            # Format the result
            output = f"## Image Analysis: {analysis_type_enum.value.capitalize()}\n\n"
            output += result.content
            
            # Add metadata if available
            if result.metadata:
                output += "\n\n### Metadata\n"
                for key, value in result.metadata.items():
                    output += f"- {key}: {value}\n"
            
            return output
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return f"Error analyzing image: {str(e)}"
    
    return {
        "name": "image_analysis",
        "description": "Analyze images to extract information, text, or understand their content.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path to the image file to analyze"
                },
                "analysis_type": {
                    "type": "string",
                    "enum": [t.value for t in AnalysisType],
                    "description": "Type of analysis to perform"
                },
                "prompt": {
                    "type": "string",
                    "description": "Optional prompt to guide the analysis"
                }
            },
            "required": ["image_path"]
        },
        "function": image_analysis_tool
    }
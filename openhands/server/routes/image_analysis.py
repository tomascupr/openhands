"""
API routes for image upload and analysis.
"""
import os
import tempfile
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from openhands.core.logger import openhands_logger as logger
from openhands.llm.llm import LLM
from openhands.server.file_config import is_extension_allowed, MAX_FILE_SIZE_MB
from openhands.server.shared import config, llm_manager
from openhands.vision.image_analyzer import AnalysisType, ImageAnalyzer

router = APIRouter()


@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    analysis_type: Optional[str] = Form("describe"),
    prompt: Optional[str] = Form(None),
) -> JSONResponse:
    """
    Upload and analyze an image.
    
    Args:
        file: The image file to upload
        analysis_type: Type of analysis to perform (describe, ocr, code, ui, diagram)
        prompt: Optional prompt to guide the analysis
        
    Returns:
        JSON response with the analysis results
    """
    # Validate the file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )
    
    # Check file extension
    if not is_extension_allowed(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed",
        )
    
    # Check file size
    if MAX_FILE_SIZE_MB > 0:
        # Read a small chunk to get the content type
        chunk = await file.read(1024)
        await file.seek(0)  # Reset file position
        
        # Check if it's actually an image
        import imghdr
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(chunk)
            temp_file.flush()
            
            image_type = imghdr.what(temp_file.name)
            if not image_type:
                os.unlink(temp_file.name)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File is not a valid image",
                )
            
            os.unlink(temp_file.name)
        
        # Check file size
        max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
        content_length = file.size
        if content_length > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB",
            )
    
    # Validate analysis type
    try:
        analysis_type_enum = AnalysisType(analysis_type.lower())
    except ValueError:
        valid_types = ", ".join([t.value for t in AnalysisType])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid analysis type. Valid types are: {valid_types}",
        )
    
    # Create a temporary file to store the image
    temp_dir = Path(config.temp_dir) / "image_analysis"
    temp_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate a unique filename
    file_extension = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid.uuid4()}{file_extension}"
    temp_path = temp_dir / temp_filename
    
    try:
        # Save the uploaded file
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Get an LLM with vision capabilities
        llm = await _get_vision_llm()
        
        # Analyze the image
        analyzer = ImageAnalyzer(llm)
        result = await analyzer.analyze(temp_path, analysis_type_enum, prompt)
        
        # Return the analysis results
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing image: {str(e)}",
        )
    finally:
        # Clean up the temporary file
        if temp_path.exists():
            os.unlink(temp_path)


async def _get_vision_llm() -> Optional[LLM]:
    """
    Get an LLM with vision capabilities.
    
    Returns:
        An LLM instance with vision capabilities, or None if not available
    """
    # Try to get a vision-capable LLM
    try:
        # First, check if there's a specific vision model configured
        if hasattr(config, "vision_model") and config.vision_model:
            return await llm_manager.get_llm(config.vision_model)
        
        # Otherwise, try to use a model that might have vision capabilities
        vision_capable_models = [
            "gpt-4-vision-preview",
            "gpt-4-vision",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "gemini-pro-vision",
        ]
        
        for model_name in vision_capable_models:
            try:
                return await llm_manager.get_llm(model_name)
            except Exception:
                continue
        
        # If no vision-capable model is available, use the default model
        # and hope it has vision capabilities
        return await llm_manager.get_llm()
    except Exception as e:
        logger.warning(f"Failed to get vision-capable LLM: {e}")
        return None
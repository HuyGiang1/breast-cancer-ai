"""
ROI (Region of Interest) preprocessing for mammogram images.
Removes background (black areas), text labels, and crops to breast region.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def extract_roi_breast(image: np.ndarray, 
                       threshold_value: int = 10,
                       margin: int = 20) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """
    Extract ROI (Region of Interest) from mammogram by removing black background and text.
    
    Args:
        image: Input grayscale or RGB mammogram image (uint8)
        threshold_value: Threshold to detect non-background pixels (default: 10)
        margin: Margin to add around detected region (default: 20)
    
    Returns:
        roi_image: Cropped image containing only breast region
        bbox: Bounding box (x_min, y_min, x_max, y_max) in original image coordinates
    """
    
    # Convert to grayscale if RGB
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    # Threshold to find non-background pixels (breast tissue is brighter than black background)
    _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        logger.warning("No contours found. Returning original image.")
        h, w = image.shape[:2]
        return image, (0, 0, w, h)
    
    # Get the largest contour (should be the breast)
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get bounding rectangle
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # Add margin but ensure it stays within image bounds
    h_img, w_img = gray.shape[:2]
    x_min = max(0, x - margin)
    y_min = max(0, y - margin)
    x_max = min(w_img, x + w + margin)
    y_max = min(h_img, y + h + margin)
    
    # Crop the image
    roi_image = image[y_min:y_max, x_min:x_max]
    
    bbox = (x_min, y_min, x_max, y_max)
    
    return roi_image, bbox


def preprocess_mammogram_roi(image_path: str,
                             target_size: Tuple[int, int] = (224, 224),
                             threshold_value: int = 10,
                             margin: int = 20) -> np.ndarray:
    """
    Load, extract ROI, and resize mammogram image to target size.
    
    Args:
        image_path: Path to mammogram image
        target_size: Target output size (height, width)
        threshold_value: Threshold for ROI detection
        margin: Margin around detected region
    
    Returns:
        Preprocessed image as numpy array (uint8, normalized to 0-255 or 0-1)
    """
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Convert BGR to RGB  
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Extract ROI
    roi_image, _ = extract_roi_breast(image, threshold_value=threshold_value, margin=margin)
    
    # Resize to target size
    resized = cv2.resize(roi_image, (target_size[1], target_size[0]))
    
    # Normalize to 0-255 (uint8) - models often expect this
    if resized.dtype != np.uint8:
        resized = np.clip(resized, 0, 255).astype(np.uint8)
    
    return resized


def batch_preprocess_images(image_dir: Path,
                            output_dir: Path,
                            target_size: Tuple[int, int] = (224, 224),
                            threshold_value: int = 10,
                            margin: int = 20) -> None:
    """
    Batch preprocess all images in a directory and save to output directory,
    preserving directory structure (benign/malignant).
    
    Args:
        image_dir: Input directory containing benign/malignant subdirectories
        output_dir: Output directory for preprocessed images
        target_size: Target output size
        threshold_value: Threshold for ROI detection
        margin: Margin around detected region
    """
    
    image_dir = Path(image_dir)
    output_dir = Path(output_dir)
    
    # Create output directory structure
    for subdir in ['benign', 'malignant']:
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Process images
    processed_count = 0
    error_count = 0
    
    for subdir in image_dir.glob('*/'):
        if subdir.name not in ['benign', 'malignant']:
            continue
        
        output_subdir = output_dir / subdir.name
        
        for image_file in subdir.glob('*.png'):
            try:
                # Preprocess image
                processed_image = preprocess_mammogram_roi(
                    str(image_file),
                    target_size=target_size,
                    threshold_value=threshold_value,
                    margin=margin
                )
                
                # Save to output directory
                output_path = output_subdir / image_file.name
                cv2.imwrite(str(output_path), cv2.cvtColor(processed_image, cv2.COLOR_RGB2BGR))
                
                processed_count += 1
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} images...")
                
            except Exception as e:
                logger.error(f"Error processing {image_file}: {e}")
                error_count += 1
    
    logger.info(f"Preprocessing complete: {processed_count} successful, {error_count} errors")


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Paths
    base_dir = Path("/Users/GiangNguyenHuy/Documents/breast-cancer-ai")
    
    # Process train set
    print("Processing train set...")
    batch_preprocess_images(
        image_dir=base_dir / "data/cbis_ddsm/processed/images/train",
        output_dir=base_dir / "data/cbis_ddsm/processed/images_roi/train"
    )
    
    # Process val set
    print("Processing validation set...")
    batch_preprocess_images(
        image_dir=base_dir / "data/cbis_ddsm/processed/images/val",
        output_dir=base_dir / "data/cbis_ddsm/processed/images_roi/val"
    )
    
    # Process test set
    print("Processing test set...")
    batch_preprocess_images(
        image_dir=base_dir / "data/cbis_ddsm/processed/images/test",
        output_dir=base_dir / "data/cbis_ddsm/processed/images_roi/test"
    )

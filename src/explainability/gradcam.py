"""
Grad-CAM (Gradient-weighted Class Activation Mapping) for Deep Learning explainability
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
import matplotlib.pyplot as plt
from typing import List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class GradCAM:
    """
    Grad-CAM implementation for CNN models (ResNet, EfficientNet, etc.)
    """
    
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        """
        Initialize Grad-CAM
        
        Args:
            model: PyTorch model
            target_layer: Target layer for CAM (usually last conv layer)
        """
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.target_layer.register_forward_hook(self.save_activation)
        self.target_layer.register_backward_hook(self.save_gradient)
    
    def save_activation(self, module, input, output):
        """Hook to save activations"""
        self.activations = output.detach()
    
    def save_gradient(self, module, grad_input, grad_output):
        """Hook to save gradients"""
        self.gradients = grad_output[0].detach()
    
    def generate_cam(
        self, 
        input_image: torch.Tensor, 
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate Class Activation Map
        
        Args:
            input_image: Input image tensor (1, C, H, W)
            target_class: Target class index (if None, uses predicted class)
            
        Returns:
            CAM as numpy array
        """
        # Forward pass
        self.model.eval()
        output = self.model(input_image)
        
        # Get target class
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Zero gradients
        self.model.zero_grad()
        
        # Backward pass
        class_score = output[:, target_class]
        class_score.backward()
        
        # Get gradients and activations
        gradients = self.gradients[0]  # (C, H, W)
        activations = self.activations[0]  # (C, H, W)
        
        # Calculate weights (global average pooling of gradients)
        weights = gradients.mean(dim=(1, 2))  # (C,)
        
        # Weighted combination of activation maps
        cam = torch.zeros(activations.shape[1:], dtype=torch.float32)
        for i, w in enumerate(weights):
            cam += w * activations[i]
        
        # ReLU
        cam = F.relu(cam)
        
        # Normalize
        cam = cam - cam.min()
        cam = cam / cam.max()
        
        return cam.cpu().numpy()
    
    def visualize_cam(
        self,
        input_image: np.ndarray,
        cam: np.ndarray,
        alpha: float = 0.5,
        colormap: int = cv2.COLORMAP_JET
    ) -> np.ndarray:
        """
        Overlay CAM on original image
        
        Args:
            input_image: Original image (H, W, C) in [0, 1] or [0, 255]
            cam: Class activation map
            alpha: Transparency of overlay
            colormap: OpenCV colormap
            
        Returns:
            Overlayed image
        """
        # Normalize input image to [0, 255]
        if input_image.max() <= 1.0:
            input_image = (input_image * 255).astype(np.uint8)
        else:
            input_image = input_image.astype(np.uint8)
        
        # Resize CAM to match input image
        h, w = input_image.shape[:2]
        cam_resized = cv2.resize(cam, (w, h))
        
        # Apply colormap
        cam_colored = cv2.applyColorMap(
            (cam_resized * 255).astype(np.uint8), 
            colormap
        )
        cam_colored = cv2.cvtColor(cam_colored, cv2.COLOR_BGR2RGB)
        
        # Overlay
        overlayed = (alpha * cam_colored + (1 - alpha) * input_image).astype(np.uint8)
        
        return overlayed
    
    def plot_gradcam(
        self,
        original_image: np.ndarray,
        cam: np.ndarray,
        prediction: str,
        confidence: float,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot Grad-CAM visualization
        
        Args:
            original_image: Original image
            cam: Class activation map
            prediction: Prediction label
            confidence: Prediction confidence
            save_path: Optional path to save figure
            
        Returns:
            Matplotlib figure
        """
        # Create overlay
        overlayed = self.visualize_cam(original_image, cam)
        
        # Create figure
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        # Original image
        axes[0].imshow(original_image if original_image.max() > 1 else (original_image * 255).astype(np.uint8))
        axes[0].set_title('Original Image', fontsize=12, fontweight='bold')
        axes[0].axis('off')
        
        # CAM heatmap
        axes[1].imshow(cam, cmap='jet')
        axes[1].set_title('Grad-CAM Heatmap', fontsize=12, fontweight='bold')
        axes[1].axis('off')
        
        # Overlay
        axes[2].imshow(overlayed)
        axes[2].set_title(f'Overlay\\nPrediction: {prediction}\\nConfidence: {confidence:.2%}',
                         fontsize=12, fontweight='bold')
        axes[2].axis('off')
        
        plt.suptitle('Grad-CAM Visualization', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Grad-CAM saved to: {save_path}")
        
        return fig


def get_target_layer(model: nn.Module, model_name: str = 'resnet50') -> nn.Module:
    """
    Get the target layer for Grad-CAM based on model architecture
    
    Args:
        model: PyTorch model
        model_name: Name of model architecture
        
    Returns:
        Target layer module
    """
    if 'resnet' in model_name.lower():
        # For ResNet: last layer of layer4
        return model.layer4[-1]
    elif 'efficientnet' in model_name.lower():
        # For EfficientNet: last conv layer
        return model.features[-1]
    elif 'vgg' in model_name.lower():
        # For VGG: last conv layer
        return model.features[-1]
    else:
        raise ValueError(f"Model {model_name} not supported. Please specify target layer manually.")


def generate_multiple_gradcams(
    model: nn.Module,
    images: List[np.ndarray],
    image_tensors: torch.Tensor,
    predictions: List[str],
    confidences: List[float],
    target_layer: nn.Module,
    save_dir: Optional[str] = None
) -> List[plt.Figure]:
    """
    Generate Grad-CAM for multiple images
    
    Args:
        model: Trained model
        images: List of original images
        image_tensors: Batch of image tensors
        predictions: List of prediction labels
        confidences: List of confidence scores
        target_layer: Target layer for Grad-CAM
        save_dir: Directory to save figures
        
    Returns:
        List of matplotlib figures
    """
    gradcam = GradCAM(model, target_layer)
    figures = []
    
    for idx, (img, img_tensor, pred, conf) in enumerate(
        zip(images, image_tensors, predictions, confidences)
    ):
        # Generate CAM
        cam = gradcam.generate_cam(img_tensor.unsqueeze(0))
        
        # Plot
        save_path = f"{save_dir}/gradcam_{idx}.png" if save_dir else None
        fig = gradcam.plot_gradcam(img, cam, pred, conf, save_path)
        figures.append(fig)
    
    return figures


# Utility: Convert model output to prediction
def get_prediction_label(output: torch.Tensor, class_names: List[str]) -> Tuple[str, float]:
    """
    Convert model output to prediction label and confidence
    
    Args:
        output: Model output tensor
        class_names: List of class names
        
    Returns:
        Tuple of (prediction_label, confidence)
    """
    probs = F.softmax(output, dim=1)
    confidence, pred_class = torch.max(probs, 1)
    
    pred_label = class_names[pred_class.item()]
    confidence_score = confidence.item()
    
    return pred_label, confidence_score

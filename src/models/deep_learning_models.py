"""
Deep Learning models for CBIS-DDSM mammography images
"""
import torch
import torch.nn as nn
import torchvision.models as models
from typing import Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class MammographyClassifier(nn.Module):
    """
    Transfer Learning classifier for mammography images
    Supports ResNet, EfficientNet architectures
    """
    
    def __init__(
        self,
        architecture: str = 'resnet50',
        num_classes: int = 2,
        pretrained: bool = True,
        freeze_backbone: bool = False
    ):
        """
        Initialize classifier
        
        Args:
            architecture: Model architecture ('resnet50', 'efficientnet_b0', etc.)
            num_classes: Number of output classes (2 for binary: benign/malignant)
            pretrained: Use ImageNet pretrained weights
            freeze_backbone: Freeze backbone weights (only train classifier)
        """
        super(MammographyClassifier, self).__init__()
        
        self.architecture = architecture
        self.num_classes = num_classes
        
        # Load backbone
        if architecture == 'resnet50':
            self.backbone = models.resnet50(pretrained=pretrained)
            in_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()  # Remove original classifier
        
        elif architecture == 'resnet18':
            self.backbone = models.resnet18(pretrained=pretrained)
            in_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        
        elif architecture == 'efficientnet_b0':
            self.backbone = models.efficientnet_b0(pretrained=pretrained)
            in_features = self.backbone.classifier[1].in_features
            self.backbone.classifier = nn.Identity()
        
        else:
            raise ValueError(f"Architecture {architecture} not supported")
        
        # Freeze backbone if requested
        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False
        
        # Custom classifier head
        self.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x: Input tensor (B, C, H, W)
            
        Returns:
            Output logits (B, num_classes)
        """
        features = self.backbone(x)
        output = self.classifier(features)
        return output
    
    def get_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extract features before classifier
        
        Args:
            x: Input tensor
            
        Returns:
            Feature tensor
        """
        return self.backbone(x)


def create_model(
    architecture: str = 'resnet50',
    num_classes: int = 2,
    pretrained: bool = True,
    freeze_backbone: bool = False
) -> MammographyClassifier:
    """
    Factory function to create mammography classifier
    
    Args:
        architecture: Model architecture
        num_classes: Number of classes
        pretrained: Use pretrained weights
        freeze_backbone: Freeze backbone
        
    Returns:
        MammographyClassifier model
    """
    model = MammographyClassifier(
        architecture=architecture,
        num_classes=num_classes,
        pretrained=pretrained,
        freeze_backbone=freeze_backbone
    )
    
    return model


class FocalLoss(nn.Module):
    """
    Focal Loss for imbalanced classification
    
    Paper: https://arxiv.org/abs/1708.02002
    """
    
    def __init__(
        self,
        alpha: Optional[torch.Tensor] = None,
        gamma: float = 2.0,
        reduction: str = 'mean'
    ):
        """
        Initialize Focal Loss
        
        Args:
            alpha: Class weights (tensor of shape [num_classes])
            gamma: Focusing parameter (higher = more focus on hard examples)
            reduction: 'mean', 'sum', or 'none'
        """
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        """
        Calculate Focal Loss
        
        Args:
            inputs: Model outputs (logits)
            targets: Ground truth labels
            
        Returns:
            Loss value
        """
        ce_loss = nn.CrossEntropyLoss(weight=self.alpha, reduction='none')(inputs, targets)
        pt = torch.exp(-ce_loss)
        focal_loss = ((1 - pt) ** self.gamma) * ce_loss
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss


def get_optimizer(
    model: nn.Module,
    optimizer_name: str = 'adam',
    learning_rate: float = 1e-4,
    weight_decay: float = 1e-5
) -> torch.optim.Optimizer:
    """
    Get optimizer for training
    
    Args:
        model: Model to optimize
        optimizer_name: 'adam', 'sgd', 'adamw'
        learning_rate: Learning rate
        weight_decay: L2 regularization
        
    Returns:
        Optimizer
    """
    if optimizer_name.lower() == 'adam':
        return torch.optim.Adam(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
    elif optimizer_name.lower() == 'adamw':
        return torch.optim.AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
    elif optimizer_name.lower() == 'sgd':
        return torch.optim.SGD(
            model.parameters(),
            lr=learning_rate,
            momentum=0.9,
            weight_decay=weight_decay
        )
    else:
        raise ValueError(f"Optimizer {optimizer_name} not supported")


def get_scheduler(
    optimizer: torch.optim.Optimizer,
    scheduler_name: str = 'cosine',
    num_epochs: int = 50
) -> torch.optim.lr_scheduler._LRScheduler:
    """
    Get learning rate scheduler
    
    Args:
        optimizer: Optimizer
        scheduler_name: 'cosine', 'step', 'plateau'
        num_epochs: Total number of epochs
        
    Returns:
        Scheduler
    """
    if scheduler_name.lower() == 'cosine':
        return torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=num_epochs
        )
    elif scheduler_name.lower() == 'step':
        return torch.optim.lr_scheduler.StepLR(
            optimizer,
            step_size=num_epochs // 3,
            gamma=0.1
        )
    elif scheduler_name.lower() == 'plateau':
        return torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode='min',
            factor=0.5,
            patience=5
        )
    else:
        raise ValueError(f"Scheduler {scheduler_name} not supported")

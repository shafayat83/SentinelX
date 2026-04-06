import torch
import torch.nn as nn
import segmentation_models_pytorch as smp

MODEL_VERSION = "2.1.0-secure"

class SpatialAttention(nn.Module):
    def __init__(self, kernel_size=7):
        super(SpatialAttention, self).__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size=kernel_size, padding=kernel_size//2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        x_concat = torch.cat([avg_out, max_out], dim=1)
        return self.sigmoid(self.conv(x_concat)) * x

class SiameseUNetPlusPlus(nn.Module):
    """
    Siamese U-Net++ Architecture for Satellite Change Detection.
    Secured and Optimized Version.
    """
    def __init__(self, in_channels=12, num_classes=1):
        super(SiameseUNetPlusPlus, self).__init__()
        
        # FIX: Instantiate the full model ONCE, then use its components.
        # Previously it was instantiated 3 times, wasting 3x VRAM.
        base_model = smp.UnetPlusPlus(
            encoder_name="efficientnet-b4",
            encoder_weights="imagenet",
            in_channels=in_channels,
            classes=num_classes
        )
        
        self.encoder = base_model.encoder
        self.decoder = base_model.decoder
        self.segmentation_head = base_model.segmentation_head
        
        # Spatial Attention Module for better temporal fusion
        self.attention = SpatialAttention()
        
        # Final classification head for change type (No Change, Deforestation, Construction, Damage)
        self.classification_head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(1792, 256), # 1792 is efficientnet-b4's final feature map channels
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 4)
        )

    def forward(self, t1, t2):
        # Process T1 and T2
        feat_t1 = self.encoder(t1)
        feat_t2 = self.encoder(t2)
        
        # Fusion Strategy: Absolute Difference + Spatial Attention
        fused_features = []
        for f1, f2 in zip(feat_t1, feat_t2):
            diff = torch.abs(f1 - f2)
            fused_features.append(self.attention(diff))
        
        # Decode
        decoded = self.decoder(*fused_features)
        
        # Change Mask (Binary)
        change_mask = self.segmentation_head(decoded)
        
        # Change Type (Multi-class)
        # We use the deepest feature map for classification
        change_type = self.classification_head(feat_t2[-1]) 
        
        return change_mask, change_type

if __name__ == "__main__":
    # Test with dummy data (Batch=1, Time=2, Bands=12, Size=512x512)
    model = SiameseUNetPlusPlus(in_channels=12, num_classes=1)
    t1 = torch.randn(1, 12, 512, 512)
    t2 = torch.randn(1, 12, 512, 512)
    mask, ctype = model(t1, t2)
    print(f"Mask shape: {mask.shape}")
    print(f"Type shape: {ctype.shape}")

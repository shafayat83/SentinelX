import torch
import torch.nn as nn
import segmentation_models_pytorch as smp

class SiameseUNetPlusPlus(nn.Module):
    """
    Siamese U-Net++ Architecture for Satellite Change Detection.
    Uses an EfficientNet-B4 backbone shared between two temporal inputs.
    """
    def __init__(self, in_channels=12, num_classes=1):
        super(SiameseUNetPlusPlus, self).__init__()
        
        # We use SMP for the base U-Net++ structure
        # Since it's Siamese, we process T1 and T2 separately and combine features
        self.encoder = smp.UnetPlusPlus(
            encoder_name="efficientnet-b4",
            encoder_weights="imagenet",
            in_channels=in_channels,
            classes=num_classes
        ).encoder
        
        self.decoder = smp.UnetPlusPlus(
            encoder_name="efficientnet-b4",
            encoder_weights="imagenet",
            in_channels=in_channels,
            classes=num_classes
        ).decoder
        
        self.segmentation_head = smp.UnetPlusPlus(
            encoder_name="efficientnet-b4",
            encoder_weights="imagenet",
            in_channels=in_channels,
            classes=num_classes
        ).segmentation_head
        
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
        # Process T1
        feat_t1 = self.encoder(t1)
        # Process T2
        feat_t2 = self.encoder(t2)
        
        # Fusion Strategy: Absolute Difference
        # In more advanced versions, we could use concatenation or dual-attention
        fused_features = [torch.abs(f1 - f2) for f1, f2 in zip(feat_t1, feat_t2)]
        
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

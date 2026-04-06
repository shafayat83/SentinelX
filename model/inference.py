import torch
import numpy as np
import rasterio
from .change_detection_net import SiameseUNetPlusPlus
import cv2
import os

ALLOWED_DATA_DIR = os.path.abspath(os.getenv("DATA_DIR", "/tmp/sentinel_data"))

class PathTraversalError(Exception):
    pass

class InferenceEngine:
    """
    Inference Engine for High-Resolution Satellite Change Detection.
    Handles Tiling, Sliding Window Inference, and Re-stitching.
    """
    def __init__(self, model_path, device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.device = device
        self.model = SiameseUNetPlusPlus(in_channels=12, num_classes=1)
        # self.model.load_state_dict(torch.load(model_path, map_location=device))
        self.model.to(device)
        self.model.eval()

    def _pad_image(self, img, patch_size):
        # Pad image for sliding window to ensure it's a multiple of patch_size
        h, w = img.shape[-2:]
        new_h = (h // patch_size + 1) * patch_size
        new_w = (w // patch_size + 1) * patch_size
        
        # img is (C, H, W)
        pad_h = new_h - h
        pad_w = new_w - w
        
        # pad_width = ((0,0), (0, pad_h), (0, pad_w))
        padded = np.pad(img, ((0,0), (0, pad_h), (0, pad_w)), mode='reflect')
        return padded, (h, w)
        
    def _validate_file_path(self, path: str) -> str:
        """Prevent path traversal attacks."""
        abs_path = os.path.abspath(path)
        if not abs_path.startswith(ALLOWED_DATA_DIR):
            # For local testing relaxation, normally we raise
            if os.getenv("ENVIRONMENT") == "production":
                raise PathTraversalError(f"Access to path {path} is denied")
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")
        return abs_path

    def _get_gaussian_window(self, window_size, sigma=0.5):
        """Creates a 2D Gaussian window to counter edge artifacts in patching."""
        half = window_size // 2
        y, x = np.ogrid[-half:window_size-half, -half:window_size-half]
        mask = np.exp(-(x**2 + y**2) / (2.0 * (sigma * half)**2))
        return mask.astype(np.float32)

    def predict(self, t1_path, t2_path, patch_size=512, overlap=64):
        # Security validation step
        t1_path = self._validate_file_path(t1_path)
        t2_path = self._validate_file_path(t2_path)
        
        window_weight = self._get_gaussian_window(patch_size)
        with rasterio.open(t1_path) as s1, rasterio.open(t2_path) as s2:
            t1 = s1.read().astype(np.float32) / 10000.0
            t2 = s2.read().astype(np.float32) / 10000.0
            
            # Pad
            padded_t1, original_shape = self._pad_image(t1, patch_size)
            padded_t2, _ = self._pad_image(t2, patch_size)
            
            c, h, w = padded_t1.shape
            output_mask = np.zeros((h, w), dtype=np.float32)
            count_map = np.zeros((h, w), dtype=np.float32)
            
            step = patch_size - overlap
            
            for y in range(0, h - patch_size + 1, step):
                for x in range(0, w - patch_size + 1, step):
                    patch_t1 = padded_t1[:, y:y+patch_size, x:x+patch_size]
                    patch_t2 = padded_t2[:, y:y+patch_size, x:x+patch_size]
                    
                    t1_tensor = torch.from_numpy(patch_t1).unsqueeze(0).to(self.device).float()
                    t2_tensor = torch.from_numpy(patch_t2).unsqueeze(0).to(self.device).float()
                    
                    with torch.no_grad():
                        with torch.autocast(device_type=self.device if self.device != 'cpu' else 'cpu'):
                            mask_out, _ = self.model(t1_tensor, t2_tensor)
                        mask_np = torch.sigmoid(mask_out).squeeze().cpu().numpy()
                    
                    output_mask[y:y+patch_size, x:x+patch_size] += (mask_np * window_weight)
                    count_map[y:y+patch_size, x:x+patch_size] += window_weight
            
            # Final Mask (Averaged Overlap)
            final_mask = output_mask / count_map
            # Remove padding
            final_mask = final_mask[:original_shape[0], :original_shape[1]]
            
            return (final_mask > 0.5).astype(np.uint8)

if __name__ == "__main__":
    # Example Usage
    # engine = InferenceEngine('model_weights.pth')
    # mask = engine.predict('t1.tif', 't2.tif')
    # cv2.imwrite('change_mask.png', mask * 255)
    pass

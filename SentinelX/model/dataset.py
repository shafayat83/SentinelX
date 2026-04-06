import torch
import torch.utils.data as data
import rasterio
import numpy as np
import os

class ChangeDetectionDataset(data.Dataset):
    """
    Dataset for Loading Bi-Temporal Sentinel-2 Imagery.
    Expects pairs of images (T1, T2) and a corresponding change mask.
    """
    def __init__(self, data_root, t1_list, t2_list, mask_list=None, transform=None):
        self.data_root = data_root
        self.t1_list = t1_list
        self.t2_list = t2_list
        self.mask_list = mask_list
        self.transform = transform

    def __len__(self):
        return len(self.t1_list)

    def _read_raster(self, path):
        with rasterio.open(path) as src:
            # Read all 12 bands
            img = src.read()
            # Normalize (S2 L2A is 16-bit uint)
            img = img.astype(np.float32) / 10000.0
            return img

    def __getitem__(self, idx):
        t1_path = os.path.join(self.data_root, self.t1_list[idx])
        t2_path = os.path.join(self.data_root, self.t2_list[idx])
        
        t1_img = self._read_raster(t1_path)
        t2_img = self._read_raster(t2_path)
        
        if self.mask_list:
            mask_path = os.path.join(self.data_root, self.mask_list[idx])
            with rasterio.open(mask_path) as src:
                mask = src.read(1) # Read first band
                # Convert to binary mask or multi-class
                mask = (mask > 0).astype(np.float32)
        else:
            mask = np.zeros_like(t1_img[0]) # Dummy mask for inference

        # Convert to Tensors
        t1_tensor = torch.from_numpy(t1_img)
        t2_tensor = torch.from_numpy(t2_img)
        mask_tensor = torch.from_numpy(mask).unsqueeze(0)
        
        if self.transform:
            # apply augmentation
            pass

        return t1_tensor, t2_tensor, mask_tensor

import xarray as xr
import numpy as np

class Preprocessor:
    """
    Geospatial Preprocessing Pipeline.
    Handles Band Stacking, Resampling, and Normalization.
    """
    def __init__(self, target_resolution=10):
        self.target_resolution = target_resolution

    def process(self, ds):
        """
        Input: xarray.Dataset (Sentinel-2 L2A)
        Process all bands to a common grid and normalize.
        """
        # Resample to target resolution
        ds_resampled = ds.rio.reproject(
            ds.rio.crs,
            resolution=self.target_resolution,
            resampling=xr.Resampling.bilinear
        )
        
        # Merge Bands into a single DataArray
        # Sentinel-2 Bands: Blue, Green, Red, NIR, etc.
        data = ds_resampled.to_array(dim="band")
        
        # Normalization (Sentinel-2 L2A is 0-10000)
        data = data.values.astype(np.float32) / 10000.0
        # Clip to [0, 1]
        data = np.clip(data, 0, 1)
        
        return data

if __name__ == "__main__":
    # Test
    # preprocessor = Preprocessor()
    # data = preprocessor.process(ds)
    # print(data.shape)
    pass

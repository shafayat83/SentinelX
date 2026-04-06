import stackstac
import pystac_client
import planetary_computer
import xarray as xr
from pyproj import Transformer
from shapely.geometry import shape
import time
import logging

MAX_AOI_AREA_KM2 = int(os.environ.get("MAX_AOI_AREA_KM2", "10000"))

class SentinelLoader:
    """
    Sentinel-2 Data Loader.
    Streams Cloud Optimized GeoTIFFs (COGs) for a given AOI and Time range.
    """
    def __init__(self, collection="sentinel-2-l2a"):
        self.catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )
        self.collection = collection

    def fetch_aoi(self, aoi_geojson, start_date, end_date, bands=["B02", "B03", "B04", "B08"]):
        """
        Fetch Sentinel-2 imagery for a given AOI and date range with retry logic.
        """
        geom = shape(aoi_geojson)
        # Approximate area check (degrees to km2 roughly at equator, for real app project to proper CRS)
        # 1 degree ^ 2 roughly 12000 km^2
        estimated_area = geom.area * 12000 
        if estimated_area > MAX_AOI_AREA_KM2:
            raise ValueError(f"AOI exceeds maximum allowed size of {MAX_AOI_AREA_KM2} km^2")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                search = self.catalog.search(
                    collections=[self.collection],
                    intersects=aoi_geojson,
                    datetime=f"{start_date}/{end_date}",
                    query={"eo:cloud_cover": {"lt": 20}},
                )
                
                items = search.item_collection()
                break # Success
            except Exception as e:
                logging.warning(f"STAC API query failed (Attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise IOError("Failed to communicate with planetary computer.")
                time.sleep(2 ** attempt)
        
        if len(items) == 0:
            return None
        
        # Select the item with the least cloud cover
        selected_item = min(items, key=lambda x: x.properties["eo:cloud_cover"])
        
        # Load using stackstac
        ds = stackstac.stack(selected_item, assets=bands)
        
        # Clip to AOI
        # To clip, we need the AOI in the CRS of the dataset (usually UTM)
        # ds_clipped = ds.raster.clip(aoi_geojson) 
        
        return ds

if __name__ == "__main__":
    # Testfetch
    # loader = SentinelLoader()
    # aoi = {"type": "Polygon", "coordinates": [[[...]]]}
    # data = loader.fetch_aoi(aoi, "2023-01-01", "2023-01-31")
    pass

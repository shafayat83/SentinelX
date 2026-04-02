import stackstac
import pystac_client
import planetary_computer
import xarray as xr
from pyproj import Transformer

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
        Fetch Sentinel-2 imagery for a given AOI and date range.
        """
        search = self.catalog.search(
            collections=[self.collection],
            intersects=aoi_geojson,
            datetime=f"{start_date}/{end_date}",
            query={"eo:cloud_cover": {"lt": 20}},
        )
        
        items = search.item_collection()
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

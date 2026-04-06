import rasterio.features
import shapely.geometry
import geopandas as gpd
import numpy as np

class Postprocessor:
    """
    Post-processing Pipeline for Change Masks.
    Vectorization, Filtering, and Simplification.
    """
    def __init__(self, min_area_m2=100, crs="EPSG:4326"):
        self.min_area_m2 = min_area_m2
        self.crs = crs

    def vectorize(self, mask, transform):
        """
        Convert a binary mask to GeoJSON polygons.
        """
        # Shapes: Generators of (shape, value)
        shapes = list(rasterio.features.shapes(
            mask.astype(np.uint8),
            mask=(mask > 0),
            transform=transform
        ))
        
        # Convert to Shapely polygons
        polygons = [shapely.geometry.shape(s) for s, v in shapes if v == 1]
        
        if not polygons:
            return gpd.GeoDataFrame(columns=["geometry"], crs=self.crs)
            
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(geometry=polygons, crs=self.crs)
        
        # Filter by area
        # Area calculation in UTM (meters)
        # Note: We should reproject to a local UTM before area filtering
        gdf_utm = gdf.to_crs(gdf.estimate_utm_crs())
        gdf["area_m2"] = gdf_utm.area
        gdf = gdf[gdf["area_m2"] >= self.min_area_m2]
        
        # Simplify geometry to reduce vertex count for Web usage
        gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.0001, preserve_topology=True)
        
        return gdf

    def to_geojson(self, gdf):
        """
        Export GeoDataFrame to GeoJSON string.
        """
        return gdf.to_json()

if __name__ == "__main__":
    # Example
    # postprocessor = Postprocessor()
    # gdf = postprocessor.vectorize(mask, transform)
    # geojson = postprocessor.to_geojson(gdf)
    pass

import random
import requests
import pyproj
import json
import matplotlib.pyplot as plt
import geopandas as gpd
from osm2geojson import json2geojson
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
import numpy as np
import contextily as cx
import datetime
import openeo
from openeo.processes import process
import os




# print("las")
class OSMFetcher:
    def __init__(self, bbox_wgs):
        self.url="https://overpass-api.de/api/interpreter"
        self.bbox_wgs=bbox_wgs
    def fetch(self):
        query = f"""
            [out:json];
            way["highway"]({self.bbox_wgs[0]},{self.bbox_wgs[1]},{self.bbox_wgs[2]},{self.bbox_wgs[3]});
            (._;>;);
            out body;
            """
        response=requests.get(self.url, params={"data":query})

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching OSM data: {response.status_code}")
            return None

class DataProcessor:
    """
    Class allowing performing spatial operations on fetched road data

    Attributes:
        osm_data: jsonified OSM Data
    """
    def __init__(self, osm_data):
        """
        Initialize with OSM data and optional road type filter.
        
        Args:
            osm_data: jsonified OSM Data
        """
        self.osm_data = osm_data
        self.allowed = ["motorway", "trunk", "primary", "secondary", "tertiary"]
        self._roads_gdf = None
        self._stop_flag=False
    def _form_gdf(self):
        """
        Creates GeoDataFrame from OSM Data
        
        Returns:
            GeoDataFrame with roads in EPSG:4326 (WGS84)
        """
        gdf = gpd.GeoDataFrame.from_features(json2geojson(self.osm_data)['features'], crs="EPSG:4326")
        return gdf

    def _filter_gdf(self):
        """
        Filters out GeoDataFrame to include only allowed road types, operation in-place
        """
        mask = self._roads_gdf["tags"].apply(lambda tags: tags["highway"] in self.allowed)
        self._roads_gdf = self._roads_gdf[mask].reset_index(drop=True)

    def _buffer_roads(self):
        """
        Apply buffer specified by road type, modify GeoDataFrame in-place, and change CRS to web mercator
        """
        def get_buffer(tags):
            """
            Gets appropriate buffer size for specific road type
            """
            highway = tags.get("highway")
            lanes = tags.get("lanes", 1)

            try:
                lanes = int(lanes)
            except (ValueError, TypeError):
                lanes = 1

            if highway in ["motorway", "trunk"]:
                return 10 * lanes
            elif highway in ["primary", "secondary", "tertiary"]:
                return 8 * lanes
            else:
                return 7 * lanes

        # buffering can happen only on geometries in meter based CRS
        self._roads_gdf = self._roads_gdf.to_crs(epsg=3857)
        self._roads_gdf["buffer_size"] = self._roads_gdf["tags"].apply(get_buffer)
        try:
            self._roads_gdf["geometry"] = self._roads_gdf.apply(lambda row: row.geometry.buffer(row["buffer_size"]), axis=1)
        except Exception as e:
            print(f"Exception{e} occured")
            self._stop_flag=True
    @property
    def roads_gdf(self):
        """
        Getter for GeoDataFrame containing roads geometries
        """
      
        if self._roads_gdf is None:
            self._roads_gdf = self._form_gdf()  
            self._filter_gdf()                   
            self._buffer_roads()                 
        
        return self._roads_gdf

    def clear_osm_cache(self):
        """
        Clears osm_data from memory
        """
        self.osm_data = None
        return True



class CoordsTransformer:
    def __init__(self, coords):
        self.coords=coords #2180
        self._wgs_coords = None
        self._mercator_coords = None

    def epsg2180_to_wgs(self):
        transformer = pyproj.Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
        min_lon, min_lat = transformer.transform(self.coords[0], self.coords[1])
        max_lon, max_lat = transformer.transform(self.coords[2], self.coords[3])
        return [min_lat, min_lon, max_lat, max_lon]
    
    def epsg_2180_to_mercator(self):
        transformer = pyproj.Transformer.from_crs("EPSG:2180", "EPSG:3857", always_xy=True)
        min_lon, min_lat = transformer.transform(self.coords[0], self.coords[1])
        max_lon, max_lat = transformer.transform(self.coords[2], self.coords[3])
        return [min_lat, min_lon, max_lat, max_lon]
    
    @property
    def wgs_coords(self):
        if self._wgs_coords is None:
            self._wgs_coords = self.epsg2180_to_wgs()
        return self._wgs_coords
    
    @property
    def mercator_coords(self):
        if self._mercator_coords is None:
            self._mercator_coords = self.epsg2180_to_mercator()
        return self._mercator_coords
    

class Rasterizer:
    def __init__(self, bbox_2180, gdf, counter, res=10):
        self.bounds = bbox_2180 
        self.res=res
        self.gdf=gdf
        self.counter=counter
        self.raster=None

    def to_raster(self):
        width = int((self.bounds[2] - self.bounds[0]) / self.res)
        height = int((self.bounds[3] - self.bounds[1]) / self.res)
        shapes = ((geom, 1) for geom in self.gdf.geometry)
        transform = rasterio.transform.from_origin(self.bounds[0], self.bounds[3], self.res, self.res)

        self.raster = rasterize(
            shapes=shapes,
            out_shape=(height, width),
            transform=transform,
            fill=0, 
            dtype='uint8')
        
      
        profile = {
            'driver': 'GTiff',
            'height': height,
            'width': width,
            'count': 1,
            'dtype': 'uint8',
            'crs': self.gdf.crs,  # or EPSG:3857 depending on your gdf CRS
            'transform': transform,
            'compress': 'lzw',
            'nodata': 0
        }

        with rasterio.open(f'dataset/masks/mask{self.counter}.tiff', 'w', **profile) as dst:
            dst.write(self.raster, 1)




        
    def viz(self):
        if self.raster is None:
            self.to_raster()
    
        plt.imshow(self.raster, cmap="gray")
        plt.title("Rasterized Vector")
        plt.show()
  


class SentinelFetcher:
    def __init__(self, bbox_wgs, counter):
        self.bbox_wgs=bbox_wgs
        self.date = datetime.date.today().strftime('%Y-%m-%d')
        self.counter=counter
    def establish_connection(self):
        self.connection = openeo.connect("https://openeo.dataspace.copernicus.eu")
        self.connection.authenticate_oidc()
    def form_query(self):
        self.cube = self.connection.load_collection(collection_id = "SENTINEL2_L2A", spatial_extent = {"west": self.bbox_wgs[1], "east": self.bbox_wgs[3], "south": self.bbox_wgs[0], "north": self.bbox_wgs[2]}, temporal_extent = ["2025-01-01", self.date], bands=["B04", "B03", "B02"], max_cloud_cover=5,)
        self.cube = self.cube.reduce_dimension(dimension="t", reducer="min")
        savere1 = self.cube.save_result(format = "GTiff")
        savere1.download(f"dataset/images/ready{self.counter}.tiff")
     



class GenerateSamples:
    def __init__(self, tile_size=2560, viz=False):
        self.tile_size = tile_size
        self.bbox_2180 = self._get_random_coords()
        self.transformer = CoordsTransformer(self.bbox_2180)
        self.viz=viz
        self._osm_data = None
        self._roads_gdf = None
        self.create_dirs()

    @staticmethod
    def create_dirs():
        if not os.path.isdir('dataset'):
            os.mkdir("dataset")
            os.mkdir("dataset/images")
            os.mkdir("dataset/masks")

    def _get_random_coords(self):
        bounds = {
            "x_min": 224127,
            "x_max": 815414,
            "y_min": 149590,
            "y_max": 758374
        }

        x_min_image = random.randrange(bounds["x_min"], bounds["x_max"] - self.tile_size)
        y_min_image = random.randrange(bounds["y_min"], bounds["y_max"] - self.tile_size)
        x_max_image = x_min_image + self.tile_size
        y_max_image = y_min_image + self.tile_size

        return [x_min_image, y_min_image, x_max_image, y_max_image]
    
    def samples(self, n=None):
        """
        Generator yielding (bbox_2180, osm_data, gdf), optionally n times (or endlessly if n=None)
        """
        count = 0
        while n is None or count < n:
            bbox_2180 = self._get_random_coords()
            transformer = CoordsTransformer(bbox_2180)
            fetcher = OSMFetcher(transformer.wgs_coords)
            osm_data = fetcher.fetch()
            processor = DataProcessor(osm_data)
            gdf = processor.roads_gdf
            stop_flag = processor._stop_flag
            sen_fetcher=SentinelFetcher(transformer.wgs_coords, count)
            if not stop_flag and gdf is not None and not gdf.empty:
                if self.viz:
                    roads_2180 = gdf.to_crs(epsg=2180)
                    rasterizer = Rasterizer(bbox_2180, roads_2180, count)
                    rasterizer.to_raster()
                    sen_fetcher.establish_connection()
                    sen_fetcher.form_query()
                yield bbox_2180, osm_data, gdf 
                count += 1
            else:
                print("Skipping sample due to processing issue.")




generator = GenerateSamples(tile_size=2560, viz=True)
for i, (bbox, osm, gdf) in enumerate(generator.samples(n=5)):
    print(f"Sample {i}  BBOX: {bbox}, Rows: {len(gdf)}")

    

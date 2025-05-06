import random
import requests
import pyproj
import json
import matplotlib.pyplot as plt
import geopandas as gpd
from osm2geojson import json2geojson
import rasterio
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
import numpy as np

def get_random_coords():
    tile_size=2560
    bounds={"x_min":224127, "x_max":815414, "y_min":149590, "y_max" :758374}

    x_min_image=random.randrange(bounds["x_min"], bounds["x_max"]-tile_size)
    y_min_image=random.randrange(bounds["y_min"], bounds["y_max"]-tile_size)
    x_max_image=x_min_image+tile_size
    y_max_image=y_min_image+tile_size

    bbox_2180=[x_min_image,y_min_image,x_max_image,y_max_image]
    return bbox_2180

bbox_2180=get_random_coords()

transformer = pyproj.Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
min_lon, min_lat = transformer.transform(bbox_2180[0], bbox_2180[1])
max_lon, max_lat = transformer.transform(bbox_2180[2], bbox_2180[3])
bbox_wgs=[min_lat, min_lon, max_lat, max_lon]


url="https://overpass-api.de/api/interpreter"

    # Query for roads
query = f"""
    [out:json];
    way["highway"]({min_lat},{min_lon},{max_lat},{max_lon});
    (._;>;);
    out body;
    """

response=requests.get(url, params={"data":query})



geojson=json2geojson(response.json())


gdf = gpd.GeoDataFrame.from_features(geojson['features'], crs="EPSG:4326")
print(gdf.columns)

# if gdf is not None:
#     fig, ax = plt.subplots(figsize=(10, 8))
#     gdf.plot(ax=ax, legend=True)
#     plt.title("Roads from OpenStreetMap")
#     plt.savefig("roads_map.png")
#     plt.show()

gdf = gdf.to_crs(3857)
# buf = roads.buffer(distance = 10000)
# bp = buf.plot()
# roads.plot(ax=bp, color='red')
# buf.plot()
tags=gdf["tags"]


allowed=["motorway", "trunk", "primary", "secondary", "tertiary"]
mask=gdf["tags"].apply(lambda tags: tags["highway"] in allowed)
gdf=gdf[mask].reset_index(drop=True)

def get_buffer_size(tags):
    type=tags["highway"]
    if "lanes" in tags:
        lanes=int(tags["lanes"])
    else:
        lanes=1

    if type == "motorway":
        buffer_size = 4*lanes
    elif type == "trunk":
        buffer_size = 4*lanes
    elif type == "primary":
        buffer_size = 5*lanes
    elif type == "secondary":
        buffer_size = 5*lanes
    elif type == "tertiary":
        buffer_size = 5*lanes
    print(buffer_size)
    return buffer_size

print(gdf)
gdf["buffer_size"] = gdf["tags"].apply(get_buffer_size)
gdf["geometry"] = gdf.apply(lambda row: row.geometry.buffer(row["buffer_size"]), axis=1)
gdf = gdf.to_crs(2180)
if gdf is not None:
    fig, ax = plt.subplots(figsize=(10, 8))
    gdf.plot(ax=ax, legend=True)
    plt.title("Roads from OpenStreetMap")
    plt.savefig("roads_map.png")
    plt.show()

# transformer = pyproj.Transformer.from_crs("EPSG:2180", "EPSG:3857", always_xy=True)
# min_lon, min_lat = transformer.transform(bbox_2180[0], bbox_2180[1])
# max_lon, max_lat = transformer.transform(bbox_2180[2], bbox_2180[3])
# bbox_3857=[min_lat, min_lon, max_lat, max_lon]



bounds = bbox_2180 
res = 10  

width = int((bounds[2] - bounds[0]) / res)
height = int((bounds[3] - bounds[1]) / res)


shapes = ((geom, 1) for geom in gdf.geometry)


transform = rasterio.transform.from_origin(bounds[0], bounds[3], res, res)
raster = rasterize(
    shapes=shapes,
    out_shape=(height, width),
    transform=transform,
    fill=0, 
    dtype='uint8'
)
plt.imshow(raster, cmap="gray")
plt.title("Rasterized Vector")
plt.show()



class GenerateSampleData:
    def __init__(self, tile_size):
        self.tile_size = tile_size
        self.bbox_2180 = self.get_random_coords()
        self.transformer=Transformations(self.bbox_2180)
        self._osmdata = None
        self._roads_gdf = None

    def get_random_coords(self):
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

    def fetch_osm_data(self):
        
        url="https://overpass-api.de/api/interpreter"
        query = f"""
            [out:json];
            way["highway"]({transformer.wgs_coords[0]},{transformer.wgs_coords[1]},{transformer.wgs_coords[2]},{transformer.wgs_coords[3]});
            (._;>;);
            out body;
            """
        response=requests.get(url, params={"data":query})

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching OSM data: {response.status_code}")
            return None
        
    def form_gdf(self):
        gdf = gpd.GeoDataFrame.from_features(self.osm_data['features'], crs="EPSG:4326")
        self.clear_osm_cache()
        return gdf
    
    @property    
    def osm_data(self):
        if self._osm_data is None:
            self._osm_data = self.fetch_osm_data()
        return self._osm_data

    @property    
    def roads_gdf(self):
        if self._roads_gdf is None:
            self._roads_gdf = self.form_gdf()
        return self._roads_gdf
    
    def clear_osm_cache(self):
        self._osm_data = None
        return True
        


class Transformations:
    def __init__(self, coords):
        self.coords=coords #2180
        self._wgs_coords = None

    def epsg2180_to_wgs(self):
        transformer = pyproj.Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
        min_lon, min_lat = transformer.transform(self.coords[0], self.coords[1])
        max_lon, max_lat = transformer.transform(self.coords[2], self.coords[3])
        return [min_lat, min_lon, max_lat, max_lon]
    
    @property
    def wgs_coords(self):
        if self._wgs_coords is None:
            self._wgs_coords = self.epsg2180_to_wgs()
        return self._wgs_coords

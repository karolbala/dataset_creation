
#  Automatic Creation of Spatial Datasets Using GIS, OSM, and Sentinel-2

This project implements a fully automated pipeline in Python that generates consistent geospatial datasets for spatial analysis or training machine learning models (e.g., semantic segmentation). It combines road network data from **OpenStreetMap** and satellite imagery from **Sentinel-2**, all processed using modern GIS libraries.

## Overview

The pipeline:
- Randomly selects locations within **Poland**.
- Downloads **road data** from OSM via the **Overpass API**.
- Retrieves **Sentinel-2 satellite imagery** via the **OpenEO API**.
- Processes and rasterizes the data to generate matching pairs of:
  - **Satellite image**
  - **Binary or multi-class road mask**

These dataset pairs can be used directly for training deep learning models or spatial analysis.

> **Why Poland?**  
> Poland was chosen as the area of interest to ensure **consistency in the spectral characteristics of roads** across samples. Sentinel-2 imagery may capture roads differently depending on surface material, lighting, or regional differences. By focusing on one country:
> - Roads share similar spectral characteristics (e.g., reflectance of asphalt).
> - Model training benefits from more uniform data.
> - Variability from different climates, land cover types, or construction standards is reduced.

## Technologies

- **Python**
- [GeoPandas](https://geopandas.org) – vector data manipulation
- [Rasterio](https://rasterio.readthedocs.io) – raster I/O and rasterization
- [PyProj](https://pyproj4.github.io/pyproj/) – coordinate reference system transformations
- [NumPy](https://numpy.org) – numerical array operations
- [Matplotlib](https://matplotlib.org) – plotting and visualizations
- [OpenEO](https://openeo.org) – access to Sentinel-2 imagery
- [OSM Overpass API](https://overpass-api.de) – road data from OpenStreetMap

## Features

###  Data Acquisition
- Fetches **road network data** from OSM using the Overpass API.
- Fetches **Sentinel-2 satellite imagery** for the same area using OpenEO.

###  Data Processing
- Converts coordinates between:
  - EPSG:2180 (Poland)
  - WGS84
  - Web Mercator
- Filters roads by type (e.g., motorway, primary, secondary).
- Creates buffers around roads (buffer size depends on road class).
- Rasterizes buffered geometries into masks matching the satellite image extent.

###  Visualization
- Optionally overlays road geometries on basemaps.

##  Output

Each generated sample includes:
- `ready.tiff` – Sentinel-2 image
- `mask.tiff` – Rasterized road mask
Saved into two diffrent directories - images, masks
## Example Use Case

Ideal for tasks like:
- Semantic segmentation
- Road detection from satellite images
- Urban planning and geospatial analytics

## TODOs / Improvements

- Add CLI for easier control
- Multi-class road masks



---

*Made with ❤️ using open source data.*

# GISTDA-Wildfire-Prediction

## Python Modules
### Sentinel-2 Image Resampling and Multi-Band Processing Script
This Python script processes Sentinel-2 imagery by resampling multiple spectral bands to a 10m resolution and then combining them into a single multi-band GeoTIFF file. The script leverages rasterio and GDAL for handling raster files, and it automates the process of finding and processing all relevant .jp2 files in a given folder structure.

Key Features:
- Resampling: The script reads each band image (e.g., B03, B04, B05) and resamples it to a 10m resolution using bilinear interpolation.
- Multi-Band Merging: After resampling, the script combines specified bands (B03, B04, B05, B06, B07, B08, B8A, B09, B12) into a single GeoTIFF file.
- Automated Folder Search: It recursively searches for folders containing Sentinel-2 .jp2 files and processes all relevant imagery automatically.
- Temporary Files Cleanup: Resampled files are stored temporarily and removed after processing to minimize storage usage.
- Output Naming: The output file is named based on the folder containing the original Sentinel-2 images, ensuring clear organization of the results.

### Burn Area Prediction and GeoTIFF Creation Script
This Python script is designed to process Sentinel-2 imagery for burn area prediction using a pre-trained LightGBM model. The script reads raster files (GeoTIFFs), applies the model to predict burnt areas, generates new GeoTIFF files with the prediction results, and outputs a GeoDataFrame with coordinates and fire date information.

Key Features:
- Prediction using LightGBM: Loads a pre-trained LightGBM model to predict burnt areas on raster image data, based on specific spectral bands.
- Preprocessing and Scaling: Normalizes raster data using a pre-fitted MinMaxScaler and prepares it for prediction.
- Chunk-based Processing: Processes large raster files in manageable chunks to optimize memory usage and ensure scalability for large datasets.
- Burn Area Extraction: Identifies and labels burnt areas from model predictions, converting raster data into polygons and extracting latitude, longitude, and fire date for each burn scar.
- Multi-Band GeoTIFF Output: Creates new GeoTIFF files with the burn predictions, preserving the original file's metadata and CRS.
- Automated Folder Search: Recursively searches directories for GeoTIFF files (with specific identifiers) and processes them.

### Polygon Extraction from Raster Data
This Python script that processes Sentinel-2 satellite imagery in raster format (GeoTIFF) to detect and extract burn areas. The burn areas are converted into vector polygons and saved as shapefiles for further geospatial analysis. Additionally, the script calculates the total burn area and provides visualizations of selected burn regions. The generated shapefiles and their related files are also zipped for easier distribution.

Key Features:
- Raster Processing: Reads the input raster file (GeoTIFF format) and identifies burn areas based on specific pixel values.
- Polygon Extraction: Converts the detected burn areas into vector polygons using raster-to-vector conversion techniques.
- Coordinate Transformation: Automatically determines the UTM zone and transforms polygons from the input CRS to UTM.
- Shapefile Creation: Saves the polygons in an ESRI Shapefile format along with their areas in square meters.
- Area Calculation: Computes the total area covered by burn scars.
- Visualization: Plots the burn condition raster and displays randomly selected polygons with their properties, including centroid coordinates and area.
- Zipping Output: Automatically zips the generated shapefile and its associated files (.shp, .shx, .dbf, .prj) for easy sharing.
- Batch Processing: Automatically processes multiple raster files in a specified folder.

How It Works:
- Input: The script processes .tif raster files from a specified folder. Each raster represents burn area conditions, where a value of 1 corresponds to a burn area.
- Labeling and Polygonization: Burn areas are identified using connected component labeling, and the corresponding regions are polygonized.
- Coordinate Handling: Each polygon's centroid is calculated, and its coordinates are converted to WGS84 (latitude and longitude). The appropriate UTM zone is automatically calculated based on the centroid.
- Output: Polygons are saved as a shapefile, with each polygon's area stored in square meters. Additionally, a plot of randomly selected polygons is displayed, and all outputs are compressed into a ZIP file.

### Sentinel-2 Image Processing Pipeline for Burn Area Detection
This repository contains a Python script that automates the processing of Sentinel-2 satellite imagery to detect burn areas. The script includes the following steps: processing the raw Sentinel-2 images, making predictions on burn areas using a machine learning model, and converting the detected burn areas into polygons for geospatial analysis. The output includes raster predictions and vector shapefiles of burn areas, with their respective area calculations.

Key Features:
- Sentinel-2 Image Processing:
The script processes Sentinel-2 images stored in a specific folder, performing necessary image preparation for burn area detection.

- Prediction of Burn Areas:
The script leverages a machine learning model to predict burn areas from the processed Sentinel-2 imagery. The predicted burn areas are output as raster files.

- Polygon Creation:
After prediction, the burn areas are extracted as polygons, which are saved in shapefile format.
The script computes the total area of the burn scars and displays random polygon properties (e.g., centroid and area).

- Automated Workflow:
The script automates the entire workflow, from image preprocessing and burn area prediction to the creation of burn area polygons and shapefile generation.

- Folder Structure:
sentinel-2 Image: The folder containing Sentinel-2 satellite imagery.
raster: The folder where processed raster images are stored after image preprocessing.
raster_output: The folder where predicted raster files are saved.
shape_polygon: The folder where generated shapefiles for detected burn areas are saved.

- Workflow Overview:
- Sentinel-2 Image Processing:
The find_and_process_folders function processes Sentinel-2 images from the specified folder (sentinel-2 Image) and saves the processed rasters in the raster folder.

- Burn Area Prediction:
The predict_main function runs a machine learning model to predict burn areas in the processed images, and saves the prediction results as .tif raster files in the raster_output folder.

- Polygon Extraction:
The create_polygon function is called for each predicted raster file, converting burn areas into polygons and saving the polygons as shapefiles in the shape_polygon folder.
The shapefiles are named according to the input raster filenames (e.g., T47QLV_20230211_predicted.shp).

- Area Calculation:
For each shapefile, the script calculates the total area of burn scars and provides properties of randomly selected polygons.

import pandas as pd # Pandas is used for handling dataframes and structured data manipulation
import numpy as np # Numpy is used for numerical operations, especially on arrays and matrices
import matplotlib.pyplot as plt # Matplotlib is used for plotting and visualizing data (e.g., maps, graphs)
import os # OS module is used for handling file and directory operations
import geopandas as gpd # Geopandas extends Pandas to support geospatial data manipulation
import random # Random module is used to generate random numbers, useful for sampling or simulations
import math # Math module provides access to mathematical functions, such as for calculations
import fiona # Fiona is used for reading and writing vector data, such as shapefiles (interacts with GeoPandas)
import rasterio # Rasterio is used for reading and writing raster files (e.g., GeoTIFF), a key tool in GIS
from shapely.geometry import shape, mapping # Shapely is used for manipulating and analyzing geometric objects such as points, lines, and polygons
from scipy.ndimage import label # Scipy's ndimage module provides image processing functions, 'label' is used for labeling connected regions
from rasterio.features import shapes # Rasterio's shapes function converts raster regions into vector shapes (useful for polygonizing raster data)
from pyproj import Transformer, CRS # Pyproj is used for handling map projections and transforming coordinates between different CRS (Coordinate Reference Systems)
import zipfile  # Use zipfile module for zipping files

def create_polygon(input_raster_path, output_shapefile_path):
    # Step 1: Read the raster file
    with rasterio.open(input_raster_path) as src:
        raster_data = src.read(1)  # Read the first band
        transform = src.transform  # Get the affine transform
        crs = src.crs  # Get the CRS of the input raster

        # Get the center coordinates of the raster
        center_x = (src.bounds.left + src.bounds.right) / 2
        center_y = (src.bounds.bottom + src.bounds.top) / 2

    # Create a transformer to convert from the raster's CRS to WGS84
    transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    # Convert center coordinates to WGS84
    center_lon, center_lat = transformer.transform(center_x, center_y)

    # Calculate the UTM zone
    utm_zone = math.floor((center_lon + 180) / 6) + 1
    hemisphere = 'north' if center_lat >= 0 else 'south'

    # Create a custom UTM CRS
    utm_crs = CRS.from_dict({
        'proj': 'utm',
        'zone': utm_zone,
        'south': hemisphere == 'south'
    })

    # Create transformer from input CRS to the appropriate UTM CRS
    transformer_to_utm = Transformer.from_crs(crs, utm_crs, always_xy=True)

    # Step 2: Extract features based on burn condition values
    burn_condition = (raster_data == 1).astype(np.uint8)

    # Label connected components
    labeled_array, num_features = label(burn_condition)

    # Step 3: Convert labeled features to polygons
    shapes_generator = shapes(labeled_array, transform=transform)

    polygons = []
    for geom, value in shapes_generator:
        if value > 0:  # Only take the features corresponding to burn condition
            polygons.append(shape(geom))

    projected_polygons = []
    for polygon in polygons:
        # Reproject polygon to UTM
        projected_polygon = shape(mapping(polygon))
        projected_polygon = shape({
            'type': 'Polygon',
            'coordinates': [
                [
                    transformer_to_utm.transform(x, y) for x, y in polygon.exterior.coords
                ]
            ]
        })
        projected_polygons.append(projected_polygon)

    # Step 4: Calculate total area and save shapefile
    total_area = sum(polygon.area for polygon in projected_polygons)

    schema = {
        'geometry': 'Polygon',
        'properties': {'id': 'int', 'area_m2': 'float'},
    }

    # Extract folder name from the shapefile path
    shapefile_folder = os.path.dirname(output_shapefile_path)

    # Create the folder if it doesn't exist
    os.makedirs(shapefile_folder, exist_ok=True)

    with fiona.open(output_shapefile_path, 'w', 'ESRI Shapefile', schema=schema, crs=crs) as shp:
        for i, polygon in enumerate(projected_polygons):
            area_m2 = polygon.area
            shp.write({
                'geometry': mapping(polygon),
                'properties': {'id': i + 1, 'area_m2': area_m2},
            })

    print(f"Shapefile saved to {output_shapefile_path}")
    print(f"Total burn area: {total_area:.2f} square meters\n")

    # Coordinate Gathering
    def get_coordinate_info(x, y):
        lon, lat = transformer.transform(x, y)
        coordinates = (lat, lon)  # Note the order: (latitude, longitude)
        return lat, lon

    # Step 5: Print properties and plot the output
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot the original raster data
    ax.imshow(raster_data, cmap='gray', extent=(transform[2], transform[2] + transform[0] * raster_data.shape[1], 
                                                transform[5] + transform[4] * raster_data.shape[0], transform[5]))
    ax.set_title("Burn Condition Raster and Random Sample of Polygons")

    # Determine the number of polygons to show (e.g., 5 or 10% of total, whichever is smaller)
    num_to_show = min(5, int(len(polygons) * 0.1))

    # Randomly select polygons to show
    polygons_to_show = random.sample(range(len(polygons)), num_to_show)

    # Plot the selected polygons and print their properties
    for i in polygons_to_show:
        polygon = polygons[i]
        x, y = polygon.exterior.xy
        ax.plot(x, y, color='red', linewidth=2)
        
        # Get centroid of the polygon
        centroid = polygon.centroid
        lat, lon = get_coordinate_info(centroid.x, centroid.y)
        area_m2 = projected_polygons[i].area  # Get area from projected polygon
        
        # Annotate the polygon with its ID
        ax.annotate(str(i+1), (centroid.x, centroid.y), color='white', fontweight='bold', ha='center', va='center')
        
        print(f"Polygon {i+1}:")
        print(f"  Centroid: ({lat:.6f}, {lon:.6f})")
        print(f"  Area: {area_m2:.4f} square meters")
        print()

    plt.tight_layout()
    plt.show()

    # Step 6: Zip the shapefile and related files
    shapefile_base = os.path.splitext(output_shapefile_path)[0]
    zip_filename = shapefile_base + '.zip'

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for ext in ['.shp', '.shx', '.dbf', '.prj']:
            filepath = shapefile_base + ext
            if os.path.exists(filepath):
                zipf.write(filepath, os.path.basename(filepath))

    print(f"Shapefile and related files zipped to {zip_filename}")

    return len(polygons), num_to_show, total_area

if __name__ == "__main__":
    # Set the root folder path where your raster files are located
    root_folder = r"raster_output"
    
    # Get all .tif files in the root folder
    raster_files = [f for f in os.listdir(root_folder) if f.endswith('.tif')]
    
    if not raster_files:
        print("No raster files found in the specified folder.")
    else:
        for raster_filename in raster_files:
            # Create the full input raster path
            input_raster_path = os.path.join(root_folder, raster_filename)
            
            # Specify the output shapefile path with the Sentinel-2 naming format
            output_shapefile_name = f"{raster_filename.split('.')[0]}.shp"  # Same name as the raster but with .shp extension
            output_shapefile_path = os.path.join('shape_polygon', output_shapefile_name)
            
            total_polygons, shown_polygons, total_area = create_polygon(input_raster_path, output_shapefile_path)
            
            print(f"Processed {raster_filename}:")
            print(f"Total number of polygons: {total_polygons}")
            print(f"Number of polygons shown: {shown_polygons}")
            print(f"Total burn area: {total_area:.2f} square meters")
import os
from sentinel_process import find_and_process_folders
from predict_module import predict_main
from create_polygon import create_polygon

def main():
    # Step 1: Process Sentinel-2 images
    root_folder = r'sentinel-2 Image'
    output_folder = r'raster'
    find_and_process_folders(root_folder, output_folder)
    
    # Step 2: Make predictions
    predict_main()
    
    # Step 3: Create polygons
    raster_output_folder = r"raster_output"
    shape_output_folder = r"shape_polygon"
    
    # Ensure the shape_output_folder exists
    os.makedirs(shape_output_folder, exist_ok=True)
    
    # Get all predicted TIF files in the raster_output folder
    raster_files = [f for f in os.listdir(raster_output_folder) if f.endswith('_predicted.tif')]
    
    for raster_filename in raster_files:
        input_raster_path = os.path.join(raster_output_folder, raster_filename)
        output_shapefile_name = f"{os.path.splitext(raster_filename)[0]}.shp"
        output_shapefile_path = os.path.join(shape_output_folder, output_shapefile_name)
        
        total_polygons, shown_polygons, total_area = create_polygon(input_raster_path, output_shapefile_path)
        
        print(f"Processed {raster_filename}:")
        print(f"Total number of polygons: {total_polygons}")
        print(f"Number of polygons shown: {shown_polygons}")
        print(f"Total burn area: {total_area:.2f} square meters")
        print()

if __name__ == "__main__":
    main()
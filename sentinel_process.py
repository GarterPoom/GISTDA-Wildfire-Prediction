import os # For handling file paths
import rasterio  # For reading and writing raster files
from rasterio.enums import Resampling  # For specifying the resampling method
from osgeo import gdal  # GDAL library for handling raster data

# Function to resample a single image to a target resolution
def resample_image(input_path, output_path, target_resolution=10):
    print(f"Resampling image: {input_path} to {output_path} at {target_resolution}m resolution.")
    
    # Open the input raster file
    with rasterio.open(input_path) as src:
        # Calculate the scale factor based on the target resolution
        scale_factor = src.res[0] / target_resolution
        
        # Read and resample the raster data
        data = src.read(
            out_shape=(
                src.count,  # Number of bands
                int(src.height * scale_factor),  # Adjusted height
                int(src.width * scale_factor)  # Adjusted width
            ),
            resampling=Resampling.bilinear  # Bilinear resampling for smooth resizing
        )
        
        # Adjust the transformation matrix to match the new resolution
        transform = src.transform * src.transform.scale(
            (src.width / data.shape[-1]),  # Adjust width scaling
            (src.height / data.shape[-2])  # Adjust height scaling
        )
        
        # Write the resampled data to a new file
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',  # Save as GeoTIFF
            height=data.shape[1],  # Set new height
            width=data.shape[2],  # Set new width
            count=src.count,  # Number of bands
            dtype=data.dtype,  # Data type (e.g., uint16)
            crs=src.crs,  # Coordinate reference system (CRS)
            transform=transform,  # New transform matrix
        ) as dst:
            dst.write(data)  # Write the resampled data
    
    print(f"Resampling completed: {output_path}")

# Function to process multiple band files in a folder
def process_bands(input_folder, output_folder):
    print(f"Processing bands in folder: {input_folder}")
    
    # Find all .jp2 files in the input folder
    jp2_files = [f for f in os.listdir(input_folder) if f.endswith('.jp2')]
    
    # Check if any .jp2 files are found
    if not jp2_files:
        print("No JP2 files found in the input folder.")
        return

    # Create a temporary folder for resampled files
    temp_folder = os.path.join(output_folder, 'temp')
    os.makedirs(temp_folder, exist_ok=True)

    resampled_files = []  # List to store paths of resampled files
    band_paths = {}  # Dictionary to hold paths for specific bands

    # Resample all images to 10m resolution
    for jp2_file in jp2_files:
        input_path = os.path.join(input_folder, jp2_file)
        output_path = os.path.join(temp_folder, f"{os.path.splitext(jp2_file)[0]}_resampled.tif")
        
        # Resample the image
        resample_image(input_path, output_path)
        resampled_files.append(output_path)

        # Store paths of specific bands (B03, B04, etc.) based on file names
        if 'B03' in jp2_file:
            band_paths['B03'] = output_path
        elif 'B04' in jp2_file:
            band_paths['B04'] = output_path
        elif 'B05' in jp2_file:
            band_paths['B05'] = output_path
        elif 'B06' in jp2_file:
            band_paths['B06'] = output_path
        elif 'B07' in jp2_file:
            band_paths['B07'] = output_path
        elif 'B08' in jp2_file:
            band_paths['B08'] = output_path
        elif 'B8A' in jp2_file:
            band_paths['B8A'] = output_path
        elif 'B09' in jp2_file:
            band_paths['B09'] = output_path
        elif 'B12' in jp2_file:
            band_paths['B12'] = output_path

    # Ensure all required bands are found
    ordered_bands = ['B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B09', 'B12']
    final_resampled_files = [band_paths[band] for band in ordered_bands if band in band_paths]

    # Create the output filename based on the input folder name
    output_filename = os.path.basename(input_folder) + '.tif'
    output_path = os.path.join(output_folder, output_filename)
    
    # Combine the resampled bands into a single multi-band GeoTIFF
    print(f"Building VRT for resampled files and translating to {output_path}.")
    vrt = gdal.BuildVRT('', final_resampled_files, separate=True)
    gdal.Translate(output_path, vrt)

    # Check the CRS of the output raster
    with rasterio.open(output_path) as dst:
        print("Output raster CRS:", dst.crs)

    # Clean up the temporary VRT file
    del vrt
    
    # Remove the temporary resampled files
    print("Cleaning up temporary files.")
    for file in resampled_files:
        os.remove(file)
    os.rmdir(temp_folder)

# Function to search for folders containing .jp2 files and process them
def find_and_process_folders(root_folder, output_folder):
    print(f"Searching for folders in: {root_folder}")
    
    # Walk through all directories and subdirectories
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # If any .jp2 files are found in the directory, process the folder
        if any(f.endswith('.jp2') for f in filenames):
            relative_path = os.path.relpath(dirpath, root_folder)  # Get the relative folder path
            current_output_folder = os.path.join(output_folder, relative_path)  # Set output folder path
            os.makedirs(current_output_folder, exist_ok=True)
            print(f"Found JP2 files in: {dirpath}. Processing...")
            process_bands(dirpath, current_output_folder)
    
    print("All folders processed.")

# Usage Example
root_folder = r'sentinel-2 Image'  # Set this to the folder containing Sentinel-2 .jp2 images
output_folder = r'raster'  # Set this to the folder where output files will be saved

# Run the folder processing function
find_and_process_folders(root_folder, output_folder)


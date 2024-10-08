import rasterio as rio # used to read, write, and analyze geospatial raster data. It's essential for handling the GeoTIFF files that contain the satellite imagery data.
import numpy as np # fundamental for handling large arrays and performing numerical operations efficiently. It allows you to manipulate the raster data as arrays, which is crucial for processing predictions and generating masks for burnt areas.
import pandas as pd # used for handling and manipulating structured data, like DataFrames. In your case, it helps with organizing the raster data and preprocessed chunks in tabular format before feeding them to the model.
import pickle # used to serialize and deserialize Python objects. You are using it to load the trained machine learning model (LightGBM) and the MinMaxScaler, which were saved as .sav and .pkl files respectively.
from collections import Counter # from the collections module helps count the occurrences of elements in an iterable. In your case, it counts the number of burnt and unburnt pixels predicted by the model.
import os # used to handle file paths, directory creation, and file operations such as finding GeoTIFF files in directories or saving new files.
import geopandas as gpd # simplifies working with geospatial data in Python. It extends pandas to support spatial operations on geometries (like polygons or points), and allows you to convert raster data into GeoDataFrames.
from shapely.geometry import shape # library for creating and manipulating geometric objects (points, lines, polygons). Here, shape() converts the raster shapes into Shapely geometries, which can then be processed further.
from rasterio.features import shapes # function is used to extract polygonal shapes from raster data, based on labeled regions or connected pixels. You use it to generate shapes from predicted burnt areas.
from scipy.ndimage import label # This function from scipy.ndimage labels connected regions in a binary mask (in your case, regions of burnt pixels). It helps in identifying and grouping connected burnt areas.
from datetime import datetime # helps in working with date and time. It is used to extract and format the fire dates from the filenames of the input raster files.
import logging # used for tracking events that happen when some software runs. In your case, it is useful for debugging and keeping track of errors or significant events during the prediction process.

# Set up logging configuration for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to process predictions and generate a GeoDataFrame containing fire events
def process_predictions(predictions, original_tif_path, fire_date=None):
    # If fire date is not provided, extract it from the filename
    if fire_date is None:
        filename = os.path.basename(original_tif_path)
        fire_date = filename.split('_')[1][:8]
        fire_date = datetime.strptime(fire_date, '%Y%m%d').strftime('%Y-%m-%d')

    # Open the original GeoTIFF file to extract metadata like transform and CRS
    with rio.open(original_tif_path) as src:
        transform = src.transform
        crs = src.crs
        height, width = src.shape

    # Reshape predictions to match the dimensions of the original raster
    raster_data = predictions.reshape((height, width))

    # Create a mask for burnt areas where prediction equals 1
    burn_condition = (raster_data == 1).astype(np.uint8)
    
    # Label connected regions of burnt pixels
    labeled_array, num_features = label(burn_condition)
    
    # Generate shapes (polygons) from labeled regions
    shapes_generator = shapes(labeled_array, transform=transform)

    # Store the polygons corresponding to burnt areas
    polygons = []
    for geom, value in shapes_generator:
        if value > 0:
            polygons.append(shape(geom))

    # Create a GeoDataFrame to hold the polygons
    gdf = gpd.GeoDataFrame(geometry=polygons, crs=crs)
    gdf = gdf.to_crs("EPSG:4326")  # Convert to WGS 84 (lat/lon)
    
    # Calculate centroids for each polygon to extract latitude and longitude
    gdf['LATITUDE'] = gdf.geometry.centroid.y
    gdf['LONGITUDE'] = gdf.geometry.centroid.x
    gdf['FIRE_DATE'] = fire_date  # Assign the fire date

    # Prepare the final result dataframe with relevant information
    result_df = gdf[['LATITUDE', 'LONGITUDE', 'FIRE_DATE']]
    
    # Count the number of burnt and unburnt pixels
    burn_count = np.sum(raster_data == 1)
    unburn_count = np.sum(raster_data == 0)

    print(result_df)
    print(f"\nCount of Burn Predicted: {burn_count}")
    print(f"Count of Unburn Predicted: {unburn_count}")

    return result_df

# Function to preprocess a chunk of data before making predictions
def preprocess_chunk(chunk, scaler):
    # Define the expected column names for each band after renaming
    expected_column_names = [
        'Band_3_Post', 'Band_4_Post', 'Band_5_Post', 'Band_6_Post',
        'Band_7_Post', 'Band_8_Post', 'Band_8A_Post', 'Band_9_Post', 'Band_12_Post'
    ]
    
    # Rename the columns of the chunk to match the expected names
    rename_dict = {f"band_{i+1}": name for i, name in enumerate(expected_column_names)}
    chunk_rename = chunk.rename(columns=rename_dict)
    
    # Extract features to be scaled using the scaler's feature names
    scaler_features = scaler.feature_names_in_
    chunk_for_scaling = chunk_rename[scaler_features]
    
    # Normalize the chunk using the provided scaler
    chunk_normalized = scaler.transform(chunk_for_scaling)
    chunk_normalized = pd.DataFrame(chunk_normalized, columns=scaler_features)
    
    return chunk_normalized

# Function to make predictions on a chunk of data using the model
def make_predictions_chunk(model, chunk):
    y_pred = model.predict(chunk)
    return y_pred

# Function to find all TIFF files in a directory
def find_tif_files(directory):
    tif_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.tif') or file.endswith('.tiff'):
                if 'T47' in file or 'T48' in file:  # Look for specific tile IDs
                    tif_files.append(os.path.abspath(os.path.join(root, file)))
    return tif_files

# Function to create a new GeoTIFF file from the predictions
def create_geotiff_from_predictions(predictions, original_tif_path, output_tif_path):
    # Ensure predictions is a numpy array before processing
    if isinstance(predictions, np.ndarray):
        predictions_array = predictions
    else:
        predictions_array = predictions.values

    # Read the metadata from the original GeoTIFF
    with rio.open(original_tif_path) as src:
        original_metadata = src.meta.copy()
    
    # Update metadata for new GeoTIFF (set dtype to uint8 and number of bands to 1)
    original_metadata.update({
        'dtype': 'uint8',
        'count': 1,
    })

    # Reshape predictions to match the original raster dimensions
    band_1 = predictions_array.reshape((original_metadata['height'], original_metadata['width']))

    # Write the predictions to a new GeoTIFF file
    with rio.open(output_tif_path, 'w', **original_metadata) as new_img:
        new_img.write(band_1, 1)

    print(f"New GeoTIFF file '{output_tif_path}' has been created.")

# Function to load a model and make predictions for the entire data
def make_predictions(directory, df_rename):
    file_path = os.path.join(directory)
    
    # Load the trained model
    loaded_model = pickle.load(open(file_path, 'rb'))
    
    # Make predictions using the model
    y_pred = loaded_model.predict(df_rename)
    
    # Store predictions in the dataframe
    df_rename["BURN_PREDICTED"] = y_pred
    df_predicted = df_rename
    
    # Count the occurrences of each predicted label
    label_counts = Counter(y_pred)
    print("\nCount of each predicted label:")
    for label, count in label_counts.items():
        print(f"Label {label}: {count}")
    
    return df_predicted

# Main function to process raster files, make predictions, and generate outputs
def predict_main():
    base_dir = r"raster"  # Directory containing input raster files
    output_dir = r"raster_output"  # Directory to store output files
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)  # Create output directory if it doesn't exist
        
    # Find all TIFF files in the base directory
    tif_files = find_tif_files(base_dir)

    try:
        for tif_file in tif_files:
            try:
                # Open the TIFF file to read its metadata and data
                with rio.open(tif_file) as src:
                    print(f"\nProcessing file: {tif_file}")
                    print("\nMetadata:")
                    for key, value in src.meta.items():
                        print(f"{key}: {value}")
                    
                    # Get image dimensions and number of bands
                    height, width = src.shape
                    n_bands = src.count
                    
                    print(f"Image dimensions: {width}x{height}")
                    print(f"Number of bands: {n_bands}")
                    
                    # Load the MinMaxScaler for normalization
                    scaler_path = r"model/min_max_scaler.pkl"
                    with open(scaler_path, 'rb') as f:
                        scaler = pickle.load(f)
                    
                    # Load the trained LightGBM model
                    model_path = r"model/Model_LGBM.sav"
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                    
                    # Set chunk size for processing large raster files in parts
                    chunk_size = 1000000
                    predictions = np.zeros((height, width), dtype=np.uint8)
                    
                    # Process raster in chunks to predict burnt areas
                    for row in range(0, height, chunk_size // width):
                        row_end = min(row + chunk_size // width, height)
                        
                        # Read a chunk of the raster data
                        chunk = src.read(window=((row, row_end), (0, width)))
                        
                        # Convert the chunk to a DataFrame and preprocess it
                        chunk_df = pd.DataFrame(chunk.reshape([n_bands, -1]).T, columns=[f"band_{i+1}" for i in range(n_bands)])
                        chunk_preprocessed = preprocess_chunk(chunk_df, scaler)
                        
                        # Make predictions for the current chunk
                        chunk_predictions = make_predictions_chunk(model, chunk_preprocessed)
                        
                        # Store predictions in the appropriate part of the result array
                        predictions[row:row_end, :] = chunk_predictions.reshape((row_end - row, width))
                    
                    print("Predictions shape:", predictions.shape)
                    
                    # Process the predictions to generate a GeoDataFrame
                    result_df = process_predictions(predictions, tif_file)
                    
                    print(f"Processing completed for {tif_file}")

                    # Create a new GeoTIFF file with the predictions
                    output_tif_path = os.path.join(output_dir, os.path.basename(tif_file).replace('.tif', '_predicted.tif'))
                    create_geotiff_from_predictions(predictions, tif_file, output_tif_path)

            except Exception as e:
                print(f"An error occurred while processing file {tif_file}: {e}")
                logger.error(f"An error occurred while processing file {tif_file}: {e}")
    finally:
        print("Success Prediction Process.")

# Run the main function when the script is executed
if __name__ == "__main__":
    predict_main()
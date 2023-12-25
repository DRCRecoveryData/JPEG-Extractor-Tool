import os
import concurrent.futures

def extract_jpeg_from_raw(raw_file_path, repaired_folder):
    with open(raw_file_path, 'rb') as raw_file:
        raw_data = raw_file.read()

        # Assuming the JPEG data is between the markers b'\xff\xd8\xff' and b'\xff\xd9'
        start_marker = b'\xff\xd8\xff'
        end_marker = b'\xff\xd9'

        start_index = raw_data.rfind(start_marker)
        end_index = raw_data.rfind(end_marker)

        if start_index != -1 and end_index != -1:
            # Extract the JPEG data
            jpeg_data = raw_data[start_index:end_index + 2]

            # Save the extracted JPEG data to a new file with the same name as RAW but with .JPG extension
            raw_file_name, _ = os.path.splitext(os.path.splitext(os.path.basename(raw_file_path))[0])
            jpeg_file_path = os.path.join(repaired_folder, raw_file_name + ".JPG")
            with open(jpeg_file_path, 'wb') as jpeg_file:
                jpeg_file.write(jpeg_data)

            print(f"JPEG data extracted from '{raw_file_path}' and saved to '{jpeg_file_path}'.")
        else:
            print(f"No JPEG data found in '{raw_file_path}'.")

def extract_jpeg_files_parallel(raw_folder_path, repaired_folder):
    # List all files in the directory
    files = [os.path.join(raw_folder_path, file) for file in os.listdir(raw_folder_path) if
             file.lower().endswith((".arw", ".cr2", ".cr3", ".nef", ".jpg"))]

    # Create the repaired folder if it doesn't exist
    if not os.path.exists(repaired_folder):
        os.makedirs(repaired_folder)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Process each RAW file concurrently
        futures = [executor.submit(extract_jpeg_from_raw, raw_file, repaired_folder) for raw_file in files]

        # Wait for all threads to finish
        concurrent.futures.wait(futures)

# Prompt user for RAW folder path
raw_folder_path = input("Enter the path to the RAW folder: ")

# Define the repaired folder path
repaired_folder = "Repaired"

# Call the function
extract_jpeg_files_parallel(raw_folder_path, repaired_folder)


#This code handles RAW files with various extensions (.arw, .cr2, .cr3, .nef, .jpg), and it should save the corresponding JPEG files with a ".JPG" extension in the "Repaired" folder.

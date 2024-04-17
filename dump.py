import os
import concurrent.futures

def extract_jpeg_from_dump(dump_file_path, output_folder):
    # Define the chunk size for reading the dump file
    chunk_size = 1024 * 1024  # 1MB

    # Open the dump file in binary mode
    with open(dump_file_path, 'rb') as dump_file:
        offset = 0
        while True:
            # Read a chunk of data from the dump file
            chunk = dump_file.read(chunk_size)
            if not chunk:
                break  # End of file reached

            # Search for JPEG markers in the chunk
            start_marker = b'\xff\xd8\xff\xdb'
            end_marker = b'\xff\xd9'
            start_index = chunk.rfind(start_marker)
            end_index = chunk.rfind(end_marker)

            if start_index != -1 and end_index != -1:
                # Extract the JPEG data
                jpeg_data = chunk[start_index:end_index + 2]

                # Generate the filename based on offset
                file_name = f"0x{offset + start_index:010X}.JPG"
                jpeg_file_path = os.path.join(output_folder, file_name)

                # Save the extracted JPEG data to a new file
                with open(jpeg_file_path, 'wb') as jpeg_file:
                    jpeg_file.write(jpeg_data)

                print(f"JPEG data extracted and saved to '{jpeg_file_path}'.")

            offset += chunk_size

def extract_jpeg_files_parallel(dump_file_path, output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit the extraction task
        executor.submit(extract_jpeg_from_dump, dump_file_path, output_folder)

# Prompt user for dump file path
dump_file_path = input("Enter the path to the dump file: ")

# Define the output folder path
output_folder = "Carved"

# Call the function
extract_jpeg_files_parallel(dump_file_path, output_folder)

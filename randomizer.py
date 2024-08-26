import os
import random
import shutil

# Set the source and destination folders
source_folder = r"C:\Users\U436445\Downloads\all_5000_dwgs\all_5000_dwgs"
dest_folder = r"Demo_DWG_In"

# Create the destination folder if it doesn't exist
os.makedirs(dest_folder, exist_ok=True)

# Function to get all .dwg files from the source folder and its subfolders
def get_dwg_files(folder):
    dwg_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith('.dwg'):
                dwg_files.append(os.path.join(root, file))
    return dwg_files

# Get all .dwg files
dwg_files = get_dwg_files(source_folder)

# Check if there are at least 30 .dwg files
if len(dwg_files) < 4:
    print(f"Error: Not enough .dwg files in the source folder and its subfolders. Found {len(dwg_files)} files.")
else:
    # Randomly select 30 files
    selected_files = random.sample(dwg_files, 30)

    # Copy the selected files to the destination folder
    for file_path in selected_files:
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(dest_folder, file_name)
        shutil.copy2(file_path, dest_path)
        print(f"Copied: {file_name}")

    print(f"Successfully copied 4 random .dwg files to {dest_folder}")
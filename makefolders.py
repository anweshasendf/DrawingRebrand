import pandas as pd
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import re

# Read the Excel file
excel_file = r"New_4550_output_file_unique_rows.xlsx"
df = pd.read_excel(excel_file)

# Define the source folders and the destination folder
source_folders = [
    #'12307_B1_DWG_Out',
    #'12307_B2_DWG_Out',
    r'C:\Users\U436445\Downloads\4550_DWG_Out\4550_DWG_Out',
    
]
destination_folder = r'Modified_4550_DWG'

# Create the destination folder if it doesn't exist
os.makedirs(destination_folder, exist_ok=True)

# Filter the dataframe to exclude 'Unmodified / Review' files
df_modified = df[~df['Filename'].str.contains('Unmodified / Review', case=False, na=False)]

# Create sets to track files
expected_files = set(df_modified['Result'].str.lower())
copied_files = set()
not_found_files = set()

# Function to find and copy a file
def find_and_copy_file(filename):
    base_name = os.path.splitext(filename)[0]  # Remove extension
    base_name_pattern = re.compile(re.escape(base_name), re.IGNORECASE)
    found = False
    for folder in source_folders:
        if os.path.exists(folder):
            try:
                for file in os.listdir(folder):
                    if base_name_pattern.search(file):
                        source_path = os.path.join(folder, file)
                        dest_path = os.path.join(destination_folder, file)
                        try:
                            shutil.copy2(source_path, dest_path)
                            print(f"Copied: {file}")
                            copied_files.add(filename.lower())
                            found = True
                            break  # Stop searching once file is found and copied
                        except Exception as e:
                            print(f"Error copying {file}: {str(e)}")
                if found:
                    break  # Stop searching other folders if file is found
            except Exception as e:
                print(f"Error accessing folder {folder}: {str(e)}")
        else:
            print(f"Folder does not exist: {folder}")
    if not found:
        print(f"File not found: {filename}")
        not_found_files.add(filename.lower())

# Use ThreadPoolExecutor for parallel processing
with ThreadPoolExecutor() as executor:
    executor.map(find_and_copy_file, df_modified['Result'])

# Find missing files
missing_files = expected_files - copied_files

print(f"Total rows in Excel: {len(df)}")
print(f"Rows after filtering 'Unmodified / Review': {len(df_modified)}")
print(f"Process completed. {len(copied_files)} files copied to '{destination_folder}'.")
print(f"Expected {len(expected_files)} files based on Excel sheet.")
print(f"Number of missing files: {len(missing_files)}")
print(f"Number of files not found in any folder: {len(not_found_files)}")

# Print missing files
print("\nMissing files:")
for file in sorted(missing_files):
    print(file)

# Print files not found
print("\nFiles not found in any folder:")
for file in sorted(not_found_files):
    print(file)

# Optionally, save missing files to a text file
with open('missing_files97ktxt', 'w') as f:
    f.write("Missing files:\n")
    for file in sorted(missing_files):
        f.write(f"{file}\n")
    f.write("\nFiles not found in any folder:\n")
    for file in sorted(not_found_files):
        f.write(f"{file}\n")

print("\nDetailed list of missing files has been saved to 'missing_files97kk.txt'")

# Check for duplicate entries in the Excel sheet
duplicates = df_modified[df_modified.duplicated(subset='Result', keep=False)]
if not duplicates.empty:
    print("\nWarning: Duplicate entries found in the Excel sheet:")
    print(duplicates['Result'])
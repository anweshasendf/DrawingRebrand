import pandas as pd
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import re 
# Read the Excel file
excel_file = r"6000_output_file_unique_rows.xlsx"
df = pd.read_excel(excel_file)

# Define the source folders and the destination folder
source_folders = [
    # 'Batch_1\B1_PDFBW_Out',
    # 'Batch_2\B2_PDFBW_out',
    # 'Batch_3\B3_PDFBW_out',
    # 'Batch_4\B4_PDFBW_Out',
    # 'Batch_5\B5_PDFBW_Out',
    # 'Batch_6\B6_PDFBW_Out',
    # 'Batch_7\B7_PDFBW_Out',
    # 'Batch_8\B8_PDFBW_Out',
    # 'Batch_9\B9_PDFBW_Out',
    # 'DS_2\DS_2_45_PDFBW_Out',
    # 'DS_2\B_123_PDFBW_Out',
    r'Modified_6000_PDF',
  
    # Add more folder paths as needed, up to 10
]
destination_folder = r'Modified_12k_NEW\12k_PDFBW_NEW'

# Create the destination folder if it doesn't exist
os.makedirs(destination_folder, exist_ok=True)

# Filter the dataframe to exclude 'Unmodified / Review' files
df_modified = df[~df['Filename'].str.contains('Unmodified / Review', case=False, na=False)]

# Create sets to track files
expected_files = set(df_modified['Result'].str.lower())
copied_files = set()

# Function to find and copy a file
def find_and_copy_file(filename):
    base_name = os.path.splitext(filename)[0]  # Remove extension
    base_name_pattern = re.compile(re.escape(base_name), re.IGNORECASE)
    found = False
    for folder in source_folders:
        try:
            for file in os.listdir(folder):
                if base_name_pattern.search(file):
                    source_path = os.path.join(folder, file)
                    dest_path = os.path.join(destination_folder, file)
                    if not os.path.exists(dest_path):
                        try:
                            shutil.copy2(source_path, dest_path)
                            print(f"Copied: {file}")
                            copied_files.add(filename.lower())
                            found = True
                        except Exception as e:
                            print(f"Error copying {file}: {str(e)}")
                    else:
                        print(f"Skipped: {file} (already exists in destination)")
                        copied_files.add(filename.lower())
                        found = True
        except Exception as e:
            print(f"Error accessing folder {folder}: {str(e)}")
    if not found:
        print(f"File not found: {filename}")

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

# Print missing files
print("\nMissing files:")
for file in sorted(missing_files):
    print(file)

# Optionally, save missing files to a text file
with open('missing_pdf_files3.txt', 'w') as f:
    for file in sorted(missing_files):
        f.write(f"{file}\n")

print("\nList of missing files has been saved to 'missing_pdf_files2.txt'")
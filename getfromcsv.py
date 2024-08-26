import pandas as pd
import os
import shutil

df = pd.read_excel(r"C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\CADRebrand\Copy of AutoCAD Drawings Review.xlsx", sheet_name='Data')

spec_names = df['Spec Name'].tolist()

source_dir = r"C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\CADRebrand\Demo_All"

# Create a new directory in the current working directory
new_dir = 'Extracted_Files'
os.makedirs(new_dir, exist_ok=True)

# Copy files with matching names to the new directory
for spec_name in spec_names:
    # Check for file with and without .dwg extension
    possible_files = [
        os.path.join(source_dir, spec_name),
        os.path.join(source_dir, spec_name + '.dwg')
    ]
    
    found_file = next((f for f in possible_files if os.path.exists(f)), None)
    
    if found_file:
        shutil.copy2(found_file, new_dir)
        print(f"Copied: {os.path.basename(found_file)}")
    else:
        print(f"File not found: {spec_name}")

print("File extraction complete.")
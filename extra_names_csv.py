import pandas as pd
import os
import shutil

def read_names(file_path, column_name):
    df = pd.read_excel(file_path)
    names = df[column_name].str.replace(r'\.(dwg|dxf)$', '', case=False, regex=True).tolist()
    return set(names)

def copy_files(source_dirs, file_names, destination):
    os.makedirs(destination, exist_ok=True)
    copied_files = []
    for source_dir in source_dirs:
        for file_name in file_names:
            for ext in ['.dwg', '.DWG']:
                source_file = os.path.join(source_dir, f"{file_name}{ext}")
                if os.path.exists(source_file):
                    shutil.copy2(source_file, destination)
                    copied_files.append(file_name)
                    break  # Stop searching if file is found
    return set(copied_files)

# Read file names from the three Excel sheets
sheet1_names = read_names(r'C:\Users\U436445\Downloads\TotalNames_10k_3.xlsx', 'Name')
sheet2_names = read_names(r"C:\Users\U436445\Downloads\5k_2.xlsx", 'Name')
sheet3_names = read_names(r'combined_output_12k_B1B2B3_insights.xlsx', 'Result')

# Find unique names in sheet1 and sheet2 that are not in sheet3
unique_names = (sheet1_names.union(sheet2_names)) - sheet3_names

# Copy the unique files to a new folder
source_directories = [r'C:\Users\U436445\Downloads\New_15']
copied_files = copy_files(source_directories, unique_names, 'Beyond_97k')

# Write actually copied unique names to a new Excel file
pd.DataFrame({'Unique Names': list(copied_files)}).to_excel('unique_names.xlsx', index=False)

print(f"Found {len(unique_names)} unique names.")
print(f"Successfully copied {len(copied_files)} unique files to the 'Beyond_97k' folder.")
print("Check 'unique_names.xlsx' for details of copied files.")
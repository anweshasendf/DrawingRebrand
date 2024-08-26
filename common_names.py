import os
import shutil

def compare_directory_contents(dir1, dir2):
    # Get file names without extensions
    files1 = {os.path.splitext(f)[0] for f in os.listdir(dir1)}
    files2 = {os.path.splitext(f)[0] for f in os.listdir(dir2)}

    # Find unique names in each directory
    unique_to_dir1 = list(files1 - files2)
    unique_to_dir2 = list(files2 - files1)

    return unique_to_dir1, unique_to_dir2

# Specify your directory paths here
dir1_path = r"Modified_4550_DWG"
dir2_path = r"Modified_4550_PDF"

unique_in_dir1, unique_in_dir2 = compare_directory_contents(dir1_path, dir2_path)

print("Files in dir1 but not in dir2:", unique_in_dir1)
print("Files in dir2 but not in dir1:", unique_in_dir2)

destination_folder = r"C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\QC_ValidationSets\Rerun PDFs B1B2"
os.makedirs(destination_folder, exist_ok=True)

for file_name in unique_in_dir1:
    source_file = os.path.join(dir1_path, file_name + ".dwg")  # Assuming PDF extension
    if os.path.exists(source_file):
        shutil.copy2(source_file, destination_folder)
        print(f"Copied: {file_name}.pdf")
    else:
        print(f"File not found: {file_name}.dwg")

print(f"Copying complete. Files copied to: {destination_folder}")
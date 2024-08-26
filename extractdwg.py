import os
import shutil

def extract_dwg_dxf(source_folder, destination_folder):
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    all_files = set()
    copied_files = set()
    not_found = set()

    # First pass: collect all file names
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            all_files.add(file)

    # Second pass: copy DWG and DXF files
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.lower().endswith(('.dwg', '.dxf')):
                file_path = os.path.join(root, file)
                try:
                    shutil.copy2(file_path, destination_folder)
                    copied_files.add(file)
                    print(f"Copied: {file_path}")
                except Exception as e:
                    print(f"Failed to copy {file_path}: {e}")

    # Find files without DWG/DXF
    for file in all_files:
        name, ext = os.path.splitext(file)
        if not any(name + e in copied_files for e in ['.dwg', '.DWG', '.dxf', '.DXF']):
            not_found.add(name)

    # Write not found files to a text file
    with open('not_found_dwg.txt', 'w') as f:
        for name in not_found:
            f.write(f"{name}\n")

    print(f"Total files: {len(all_files)}")
    print(f"Copied DWG/DXF files: {len(copied_files)}")
    print(f"Files without DWG/DXF: {len(not_found)}")
    print(f"List of files without DWG/DXF saved to 'not_found_dwg3.txt'")

source_folder = input("Enter the source folder path: ")
destination_folder = input("Enter the destination folder path: ")

extract_dwg_dxf(source_folder, destination_folder)
print("Extraction complete!")


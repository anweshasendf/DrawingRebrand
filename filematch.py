import os
import shutil
from collections import defaultdict

def compare_and_copy_directories(dir1, dir2, copy_dir):
    # Get file names (without extensions) for each directory
    files_dir1 = set(os.path.splitext(f)[0] for f in os.listdir(dir1))
    files_dir2 = set(os.path.splitext(f)[0] for f in os.listdir(dir2))

    # Find files missing in dir2 but present in dir1
    missing_in_dir2 = files_dir1 - files_dir2

    # Create the copy directory if it doesn't exist
    os.makedirs(copy_dir, exist_ok=True)

    # Copy missing files from dir1 to copy_dir
    copied_files = []
    for file in missing_in_dir2:
        # Find the original file with extension in dir1
        original_file = next((f for f in os.listdir(dir1) if os.path.splitext(f)[0] == file), None)
        if original_file:
            src_path = os.path.join(dir1, original_file)
            dst_path = os.path.join(copy_dir, original_file)
            shutil.copy2(src_path, dst_path)
            copied_files.append(original_file)

    # Print results
    print("Comparison and Copy Results:")
    print("-----------------------------")
    print(f"\nFiles missing in {dir2} but present in {dir1}:")
    if copied_files:
        for file in sorted(copied_files):
            print(f"  - {file}")
        print(f"\nTotal files copied to {copy_dir}: {len(copied_files)}")
    else:
        print("  No files missing in dir2.")

    return copied_files

# Example usage
if __name__ == "__main__":
    # You can modify these paths as needed
    dir1 = r"Batch_8\Batch_8_DXF_Out"
    dir2 = r"Batch_8\B8_PDF_Out"
    copy_dir = r"Batch_8\B8_MissingPDF_Files"  # New directory to copy missing files

    compare_and_copy_directories(dir1, dir2, copy_dir)
import os
import shutil
import csv
from datetime import datetime

def copy_missing_files(missing_files_path, source_dirs, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    log_file = f"copy_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Filename', 'Error'])

        with open(missing_files_path, 'r') as missing_files:
            for filename in missing_files:
                filename = filename.strip()
                if filename.lower().endswith('.dxf'):
                    file_found = False
                    for source_dir in source_dirs:
                        source_path = os.path.join(source_dir, filename)
                        if os.path.exists(source_path):
                            dest_path = os.path.join(output_dir, filename)
                            try:
                                shutil.copy2(source_path, dest_path)
                                print(f"Copied {filename} from {source_dir} to {output_dir}")
                                file_found = True
                                break
                            except Exception as e:
                                error_message = str(e)
                                print(f"Error copying {filename} from {source_dir}: {error_message}")
                                csv_writer.writerow([filename, error_message])
                    
                    if not file_found:
                        error_message = "File not found in any source directory"
                        print(f"File not found: {filename}")
                        csv_writer.writerow([filename, error_message])

# Example usage
missing_files_path = "missing_pdf_files2.txt"
source_directories = [
    '12307_B1_DXF_Out',
    '12307_B2_DXF_Out',
    '12307_B3_DXF_Out',
]
output_directory = r"Rerun PDFs B1B2"

copy_missing_files(missing_files_path, source_directories, output_directory)
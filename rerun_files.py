import pandas as pd
import shutil
import os
import openpyxl

def load_insights(excel_file):
    # Load the "Files Review Detail" sheet from the Excel file
    wb = openpyxl.load_workbook(excel_file)
    ws = wb["Files Review Detail"]
    
    # Convert worksheet to DataFrame
    data = ws.values
    columns = next(data)[0:]
    df = pd.DataFrame(data, columns=columns)
    
    # Filter for files marked as "Send to Review"
    return df[df['Issue'] == "Send to Review"]

def reinitialize_directory(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)
    print(f"Reinitialized {directory}")

def copy_files_to_rerun(files_to_review, input_dir, rerun_dir):
    if not os.path.exists(rerun_dir):
        os.makedirs(rerun_dir)

    # Copy each file to the Rerun_directory
    copied_count = 0
    for _, row in files_to_review.iterrows():
        filename = row['Filename']
        source_path = os.path.join(input_dir, filename)
        dest_path = os.path.join(rerun_dir, filename)

        try:
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_path)
                print(f"Copied {filename} to Rerun_directory (Send to Review)")
                copied_count += 1
            else:
                print(f"Warning: {filename} not found in input directory")
        except Exception as e:
            print(f"Error copying {filename}: {str(e)}")

    print(f"Copied {copied_count} files to Rerun_directory")

def main():
    excel_file = 'ComparisonOutput\comprehensive_quality_check4_with_insights.xlsx'
    input_dir = 'Demo_DXF_Out'
    rerun_dir = 'Rerun_directory'
    
    reinitialize_directory(rerun_dir)

    files_to_review = load_insights(excel_file)
    copy_files_to_rerun(files_to_review, input_dir, rerun_dir)

if __name__ == '__main__':
    main()
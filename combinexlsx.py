import os
import pandas as pd
from openpyxl import load_workbook

def combine_xlsx_files(folder_path, output_file):
    # Get all xlsx files in the specified folder
    xlsx_files = [f for f in os.listdir(folder_path) if f.endswith('.xlsx')]
    
    if not xlsx_files:
        print("No xlsx files found in the specified folder.")
        return
    
    # Load the first file to get the structure
    first_file = os.path.join(folder_path, xlsx_files[0])
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Read all sheets from the first file
        with pd.ExcelFile(first_file) as xls:
            sheet_names = xls.sheet_names
            for sheet_name in sheet_names:
                df = pd.read_excel(xls, sheet_name)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    # Append data from other files
    for file in xlsx_files[1:]:
        file_path = os.path.join(folder_path, file)
        print(f"Processing file: {file}")
        
        with pd.ExcelFile(file_path) as xls:
            for sheet_name in sheet_names:
                df = pd.read_excel(xls, sheet_name)
                
                # Add a separator row
                separator_row = pd.DataFrame([['---Next File---'] * len(df.columns)], columns=df.columns)
                df = pd.concat([separator_row, df], ignore_index=True)
                
                # Append to the existing sheet
                book = load_workbook(output_file)
                writer = pd.ExcelWriter(output_file, engine='openpyxl', mode='a', if_sheet_exists='overlay')
                
                existing_df = pd.read_excel(output_file, sheet_name=sheet_name)
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                
                combined_df.to_excel(writer, sheet_name=sheet_name, index=False)
                writer.close()
    
    print(f"Combined Excel file created: {output_file}")

# Usage
folder_path = r'XLSX_B1B2'  # Replace with your folder path
output_file = 'combined_output_12k_B1B2B3_insights.xlsx'

combine_xlsx_files(folder_path, output_file)
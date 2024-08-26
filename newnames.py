import pandas as pd
import re

# Read the Excel file
xlsx_df = pd.read_excel(r"C:\Users\U436445\Downloads\combined_output_15k_insights_updated.xlsx", sheet_name='Files Review Detail')

# Read the CSV file
csv_df = pd.read_csv(r'C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\QC_ValidationSets\file_names2.csv')

def clean_filename(filename):
    # Remove 'CAD Drawing_ ' prefix and file extensions
    cleaned = re.sub(r'^cad drawing_', '', filename, flags=re.IGNORECASE)
    cleaned = re.sub(r'\.(dxf|dwg)$', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip().lower()

# Extract and clean filenames from both sources
xlsx_filenames = xlsx_df['Result'].apply(clean_filename)
csv_filenames = csv_df['File Name'].apply(clean_filename)

# Create dictionaries to map cleaned names to original names
xlsx_map = dict(zip(xlsx_filenames, xlsx_df['Filename']))
csv_map = dict(zip(csv_filenames, csv_df['File Name']))

# Find filenames that are in xlsx but not in csv
xlsx_only = set(xlsx_filenames) - set(csv_filenames)

# Find filenames that are in csv but not in xlsx
csv_only = set(csv_filenames) - set(xlsx_filenames)

# Combine the results
missing_files = pd.DataFrame({
    'File Name': [xlsx_map.get(name, csv_map.get(name)) for name in xlsx_only.union(csv_only)],
    'Cleaned Name': list(xlsx_only.union(csv_only)),
    'Source': ['XLSX' if name in xlsx_only else 'CSV' for name in xlsx_only.union(csv_only)]
})

# Sort the results alphabetically by cleaned filename
missing_files = missing_files.sort_values('Cleaned Name')

# Write the results to a new CSV file
missing_files.to_csv('missing_files.csv', index=False)

print(f"Found {len(xlsx_only)} files only in XLSX and {len(csv_only)} files only in CSV.")
print("Results have been written to 'missing_files.csv'")
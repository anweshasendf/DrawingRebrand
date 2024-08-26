import pandas as pd
import re 

# Read the original Excel file
input_file = r"4550_output_file_unique_rows.xlsx"
output_file = r'New_4550_output_file_unique_rows.xlsx'

# Read the "Files Review Detail" sheet from the Excel file
df = pd.read_excel(input_file, sheet_name="Files Review Detail")

# Remove duplicate rows
df_unique = df.drop_duplicates()

# Create a mask for rows with 'Unmodified / Review' in Filename
unmodified_mask = df_unique['Filename'].str.contains('Unmodified', case=False, na=False)

# Create a mask for rows with 'Modified file (elements changed)' in Filename
modified_mask = df_unique['Filename'].str.contains('Modified file \(elements changed\)', case=False, na=False)

# Group by 'Result' and check if both 'Unmodified' and 'Modified' exist
duplicates = df_unique.groupby('Result').apply(lambda x: (unmodified_mask[x.index].any() and modified_mask[x.index].any()))

# Create a mask for rows to keep
keep_mask = ~(modified_mask & df_unique['Result'].isin(duplicates[duplicates].index))

# Filter the DataFrame
df_unique = df_unique[keep_mask]

def contains_chinese(text):
    if isinstance(text, str):
        return bool(re.search('[\u4e00-\u9fff]', text))
    return False


# Apply the new logic
numeric_columns = ['Text', 'Logo', 'IP Change', 'Division']
for col in numeric_columns:
    df_unique[col] = pd.to_numeric(df_unique[col], errors='coerce')

# Apply the new logic
mask = (
    (df_unique['Filename'].str.contains('Modified file \(elements changed\)|Modified', case=False, na=False)) &
    (df_unique['Block Changes'].str.contains('No significant block changes detected', case=False, na=False)) 
) | (
    (df_unique['Filename'].str.contains('Danfoss File', case=False, na=False)) &
    (df_unique['Logo'].fillna(0) == 0) &
    (df_unique['Division'].fillna(0) == 0) &
    (df_unique['IP Change'].fillna(0) == 0) &
    (df_unique['Text'].fillna(0) >= 1)
) | (
    # New condition 1
    (df_unique['Filename'].str.contains('Danfoss File', case=False, na=False)) &
    ((df_unique['Logo'].fillna(0) > 0) | (df_unique['IP Change'].fillna(0) > 0) | (df_unique['Division'].fillna(0) > 0)) &
    (df_unique['Extra Checks in DWG'].str.contains('All Extra checks passed', case=False, na=False)) &
    (df_unique['Result'].str.startswith(('GH', 'GA'), na=False))
) | (
    # New condition 2
    (df_unique['Filename'].str.contains('Modified file \(elements changed\)', case=False, na=False)) &
    (df_unique['Issue'].str.contains('Aeroquip file detected', case=False, na=False) | (df_unique['IP Change'].fillna(0) > 1))
) | (
    # New condition 3
    (df_unique['IP Change'].fillna(0) == 0) &
    (df_unique['Logo'].fillna(0) == 0) &
    (df_unique['Division'].fillna(0) == 0) &
    (df_unique['Text'].fillna(0) == 0) &
    (df_unique['Block Changes'].str.contains('(GDJT-|MFG-JT-).+[\u4e00-\u9fff]', case=False, na=False))
)


pdf_error_mask = (
    df_unique['Block Changes'].apply(contains_chinese) &
    df_unique['Filename'].str.contains('Modified file \(elements changed\)|Modified|Danfoss File', case=False, na=False)
)

df_unique.loc[mask, 'Filename'] = 'Unmodified / Review'
df_unique.loc[pdf_error_mask, 'Filename'] = 'PDF Error'

df_unique['Original_Classification'] = df_unique['Filename']

df_unique.loc[df_unique['Filename'] == 'PDF Error', 'Filename'] = 'Unmodified / Review'



# Save the modified DataFrame to a new Excel file
df_unique.to_excel(output_file, index=False, sheet_name="Files Review Detail")

print(f"Original sheet 'Files Review Detail' had {len(df)} rows.")
print(f"New file has {len(df_unique)} unique rows.")
print(f"Removed {len(df) - len(df_unique)} duplicate rows.")
print(f"Modified {mask.sum()} rows to 'Unmodified / Review'.")
print(f"Identified {pdf_error_mask.sum()} rows as 'PDF Error' (saved as 'Unmodified / Review').")
print(f"Removed {(~keep_mask).sum()} rows with 'Modified' where 'Unmodified' exists.")
print(f"Modified data saved to {output_file}")
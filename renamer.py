import os
import re
import shutil

def clean_filename(filename):
    # Split the filename at the last hyphen or underscore
    parts = re.split(r'[-_](?=[^-_]*$)', filename)
    base = parts[0]
    extension = parts[1] if len(parts) > 1 else ''

    # Remove specified extensions from the last part
    pattern = r'^(?:layout\d*|model|[Aa][1-4](?:\s*[Mm][Aa][Uu][Mm][Ee][Ee])?|sheet\s*\d+)(?:\s*\(\d+\))?$'
    if re.match(pattern, extension, re.IGNORECASE):
        return base
    return filename

def rename_pdfs(pdf_folder, dwg_folder):
    dwg_files = set(clean_filename(f.lower().replace('.dwg', '')) for f in os.listdir(dwg_folder) if f.lower().endswith('.dwg'))
    
    for filename in os.listdir(pdf_folder):
        if filename.lower().endswith('.pdf'):
            name_without_ext = os.path.splitext(filename)[0]
            cleaned_name = clean_filename(name_without_ext)
            
            if cleaned_name.lower() in dwg_files:
                new_filename = f"{cleaned_name}.pdf"
                if new_filename != filename:
                    old_path = os.path.join(pdf_folder, filename)
                    new_path = os.path.join(pdf_folder, new_filename)
                    
                    # If the new filename already exists, create a copy with a suffix
                    counter = 1
                    while os.path.exists(new_path):
                        new_filename = f"{cleaned_name} ({counter}).pdf"
                        new_path = os.path.join(pdf_folder, new_filename)
                        counter += 1
                    
                    # Rename the file instead of copying
                    os.rename(old_path, new_path)
                    print(f"Renamed: {filename} -> {new_filename}")

# Usage
pdf_folder = r"C:\Users\U436445\Downloads\ModifiedALLPDF\Modified_New_25k_PDFBW"
dwg_folder = r"C:\Users\U436445\Downloads\ModifiedAllDWG10kand15k\Modified_New_DWG_25k"
rename_pdfs(pdf_folder, dwg_folder)
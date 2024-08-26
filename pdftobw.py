import os
import shutil
import fitz  # PyMuPDF
from PIL import Image
import io

def convert_pdf_to_bw(input_folder, output_folder, replace=False):
    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")
    print(f"Replace mode: {'On' if replace else 'Off'}")

    if not os.path.exists(input_folder):
        print(f"The input folder {input_folder} does not exist.")
        return
    
    if not replace and not os.path.exists(output_folder):
        print(f"Creating output folder: {output_folder}")
        os.makedirs(output_folder)

    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
    print(f"Found {len(pdf_files)} PDF files in the input folder.")

    unconverted_files = []

    for filename in pdf_files:
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(input_folder if replace else output_folder, filename)
        
        print(f"Processing: {filename}")
        
        try:
            # Open the PDF
            doc = fitz.open(input_path)
            
            # Create a new PDF document
            new_doc = fitz.open()
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                print(f"  Processing page {page_num + 1}")
                
                # Convert page to high-resolution image
                zoom = 4  # Increase resolution
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Convert to black and white with adjusted threshold
                bw_img = img.convert('L')
                bw_img = bw_img.point(lambda x: 0 if x < 200 else 255, '1')  # Adjusted threshold
                
                # Convert back to PDF page
                imgByteArr = io.BytesIO()
                bw_img.save(imgByteArr, format='PNG', dpi=(300*zoom, 300*zoom))
                imgByteArr.seek(0)
                
                # Create a new page in the new document
                new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
                
                # Insert the black and white image into the new page
                new_page.insert_image(new_page.rect, stream=imgByteArr.getvalue())
            
            # Save the new PDF
            new_doc.save(output_path)
            new_doc.close()
            doc.close()
            
            print(f"Converted {filename} to black and white.")
        except Exception as e:
            print(f"An error occurred while processing {filename}: {str(e)}")
            unconverted_files.append(filename)
            if not replace:
                # Copy the original file to the output folder only if not in replace mode
                shutil.copy2(input_path, output_path)
                print(f"Copied original file {filename} to output folder.")

    if unconverted_files:
        print("\nThe following files were not converted and were copied to the output folder:")
        for file in unconverted_files:
            print(f"- {file}")
    else:
        print("\nAll files were successfully converted.")

if __name__ == "__main__":
    input_folder = input("Enter the input folder path containing PDF files: ")
    replace = input("Do you want to replace the original files? (y/n): ").lower() == 'y'
    
    if replace:
        output_folder = input_folder
    else:
        output_folder = input("Enter the output folder path for converted PDFs: ")
    
    convert_pdf_to_bw(input_folder, output_folder, replace)

print("Script execution completed.")

if __name__ == "__main__":
    input_folder = input("Enter the input folder path containing PDF files: ")
    output_folder = input("Enter the output folder path for converted PDFs: ")
    convert_pdf_to_bw(input_folder, output_folder)

print("Script execution completed.")
#C:\Users\U436445\OneDrive - Danfoss\Desktop\PDFsMissingB1_15k
#C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\QC_ValidationSets\Modifiedof15k_PDF
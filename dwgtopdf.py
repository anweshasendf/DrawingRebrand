import os
import subprocess
import csv
from datetime import datetime

def create_batch_file(acad_exe_path, input_dwg, output_pdf, script_path):
    batch_content = f"""
@echo off
echo Input DWG: {input_dwg}
echo Output PDF: {output_pdf}
"{acad_exe_path}" /i "{input_dwg}" /s "{script_path}"
if exist "{output_pdf}" (
    echo Conversion successful: {output_pdf}
) else (
    echo Conversion failed: {output_pdf} not found
)
"""
    batch_path = os.path.abspath("convert_dwg2.bat")
    with open(batch_path, "w") as batch_file:
        batch_file.write(batch_content)
    return batch_path

def convert_dwg_to_pdf(acad_exe_path, input_dwg, output_pdf):
    # Create a temporary script file
    script_content = f"""
_PLOT
_Y
Layout1
DWG To PDF.pc3
ANSI full bleed A (8.50 x 11.00 Inches)
_Inches
_Landscape
_No
_Extents
_Fit
0,0
_Yes
.
_Yes
_N
_N
_Y
"{output_pdf}"
_N
_Y
"""
    script_path = os.path.abspath("temp_plot_script2.scr")
    with open(script_path, "w") as script_file:
        script_file.write(script_content)

    # Create and run the batch file
    batch_path = create_batch_file(acad_exe_path, input_dwg, output_pdf, script_path)
    try:
        result = subprocess.run(batch_path, shell=True, check=True, capture_output=True, text=True)
        print(f"Batch file output:\n{result.stdout}")
        print(f"Batch file errors:\n{result.stderr}")
        
        if "Conversion failed" in result.stdout:
            return f"AutoCAD conversion failed: {output_pdf} not found"
        if not os.path.exists(output_pdf):
            return f"PDF file was not created at {output_pdf}"
        return None
    except subprocess.CalledProcessError as e:
        return f"Error running batch file: {e}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    finally:
        # Clean up temporary files
        for file in [script_path, batch_path]:
            if os.path.exists(file):
                os.remove(file)

def process_directory(acad_exe_path, input_dir, output_dir):
    # Create output directory if it doesn't exist
    input_dir = os.path.abspath(input_dir)
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")

    # Create a CSV file for error logging
    log_file = f"conversion_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Filename', 'Error'])

        # Process all DWG files in the input directory
        for filename in os.listdir(input_dir):
            if filename.lower().endswith('.dwg'):
                input_path = os.path.join(input_dir, filename)
                output_filename = os.path.splitext(filename)[0] + '.pdf'
                output_path = os.path.join(output_dir, output_filename)
                
                print(f"Converting {filename} to PDF...")
                error = convert_dwg_to_pdf(acad_exe_path, input_path, output_path)
                if error:
                    print(f"Error converting {filename}: {error}")
                    csv_writer.writerow([filename, error])
                else:
                    print(f"Converted {filename} to {output_filename}")

# Example usage
acad_exe_path = r"C:\CAD\Autodesk\AutoCAD 2022\accoreconsole.exe"
input_directory = r"Modified_4550_DWG"
output_directory = r"Modified_4550_PDF"

process_directory(acad_exe_path, input_directory, output_directory)
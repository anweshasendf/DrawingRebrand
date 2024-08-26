import os
import subprocess
import csv
from datetime import datetime
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFHandler(FileSystemEventHandler):
    def __init__(self, output_pdf):
        self.output_pdf = output_pdf
        self.pdf_created = False

    def on_created(self, event):
        if not event.is_directory and event.src_path == self.output_pdf:
            logger.info(f"PDF file created: {self.output_pdf}")
            self.pdf_created = True

def convert_dwg_to_pdf(acad_exe_path, input_dwg, output_pdf):
    logger.info(f"Starting conversion of {input_dwg}")
    script_content = f"""
_PLOT
_Y
Layout1
DWG To PDF.pc3
ISO full bleed A4 (297.00 x 210.00 MM)
_Millimeters
_Landscape
_No
_Window
0,0,0
420,297,0
_Fit
_Center
_Yes
.
_Yes
_No
_Yes
_No
"{output_pdf}"
_No
_Yes
_Yes
"""
    script_path = os.path.abspath("temp_plot_script_dwg.scr")
    with open(script_path, "w") as script_file:
        script_file.write(script_content)

    batch_path = create_dwg_batch_file(acad_exe_path, input_dwg, output_pdf, script_path)
    
    try:
        logger.info(f"Running batch file: {batch_path}")
        start_time = time.time()
        
        # Set up file watcher
        event_handler = PDFHandler(output_pdf)
        observer = Observer()
        observer.schedule(event_handler, path=os.path.dirname(output_pdf), recursive=False)
        observer.start()

        # Run the batch file
        process = subprocess.Popen(batch_path, shell=True)
        
        # Wait for the process to complete or the PDF to be created
        while process.poll() is None and not event_handler.pdf_created:
            time.sleep(1)
        
        observer.stop()
        observer.join()
        
        end_time = time.time()
        logger.info(f"Batch file execution time: {end_time - start_time:.2f} seconds")
        
        if not os.path.exists(output_pdf):
            return f"PDF file was not created at {output_pdf}"
        elif os.path.getsize(output_pdf) == 0:
            return f"PDF file was created but is empty: {output_pdf}"
        return None
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    finally:
        # Clean up temporary files
        for file in [script_path, batch_path]:
            if os.path.exists(file):
                os.remove(file)

def create_dwg_batch_file(acad_exe_path, input_dwg, output_pdf, script_path):
    batch_content = f"""
@echo on
echo Input DWG: {input_dwg}
echo Output PDF: {output_pdf}
"{acad_exe_path}" /i "{input_dwg}" /s "{script_path}"
if exist "{output_pdf}" (
    echo Conversion successful: {output_pdf}
    for %%I in ("{output_pdf}") do echo File size: %%~zI bytes
) else (
    echo Conversion failed: {output_pdf} not found
)
if exist acad.err (
    echo AutoCAD Error Log:
    type acad.err
) else (
    echo No AutoCAD error log found.
)
"""
    batch_path = os.path.abspath("convert_dwg.bat")
    with open(batch_path, "w") as batch_file:
        batch_file.write(batch_content)
    return batch_path

def process_dwg_directory(acad_exe_path, input_dir, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")

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
                
                logger.info(f"Converting {filename} to PDF...")
                error = convert_dwg_to_pdf(acad_exe_path, input_path, output_path)
                if error:
                    logger.error(f"Error converting {filename}: {error}")
                    csv_writer.writerow([filename, error])
                else:
                    logger.info(f"Converted {filename} to {output_filename}")

    logger.info("Conversion process completed.")

# Example usage
acad_exe_path = r"C:\CAD\Autodesk\AutoCAD 2022\accoreconsole.exe"
input_directory = r"Batch_1\Batch_1_DWG_Out"
output_directory = r"Batch_1\B1_DXF_PDF_Out"

process_dwg_directory(acad_exe_path, input_directory, output_directory)
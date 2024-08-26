import os
import subprocess
import csv
from datetime import datetime
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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

def convert_dxf_to_pdf(acad_exe_path, input_dxf, output_pdf):
    logger.info(f"Starting conversion of {input_dxf}")
    script_content = f"""
_PLOT
_Y
Model
DWG To PDF.pc3
ISO full bleed A4 (297.00 x 210.00 MM)
_Millimeters
_Landscape
_No
_Extents
_Fit
_Center
_Yes
.
_Yes
_No
_Yes
_No
"{output_pdf}"
_Yes
"""
    script_path = os.path.abspath("temp_plot_script_dxf.scr")
    with open(script_path, "w") as script_file:
        script_file.write(script_content)

    batch_path = create_dxf_batch_file(acad_exe_path, input_dxf, output_pdf, script_path)
    
    try:
        logger.info(f"Running batch file: {batch_path}")
        start_time = time.time()
        
        process = subprocess.Popen(batch_path, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        timeout = 50  # Increase timeout to 120 seconds
        while process.poll() is None and time.time() - start_time < timeout:
            time.sleep(1)
            logger.info(f"Waiting for conversion... Time elapsed: {time.time() - start_time:.2f} seconds")
        
        if process.poll() is None:
            logger.warning("Process timed out, terminating...")
            process.terminate()
        
        stdout, stderr = process.communicate()
        logger.info(f"Process output: {stdout.decode('utf-8')}")
        if stderr:
            logger.error(f"Process error: {stderr.decode('utf-8')}")
        
        end_time = time.time()
        logger.info(f"Batch file execution time: {end_time - start_time:.2f} seconds")
        
        if not os.path.exists(output_pdf):
            return f"PDF file was not created at {output_pdf}"
        elif os.path.getsize(output_pdf) == 0:
            return f"PDF file was created but is empty: {output_pdf}"
        return None
    except Exception as e:
        logger.exception(f"Unexpected error during conversion: {str(e)}")
        return f"Unexpected error: {str(e)}"
    finally:
        for file in [script_path, batch_path]:
            if os.path.exists(file):
                os.remove(file)

def create_dxf_batch_file(acad_exe_path, input_dxf, output_pdf, script_path):
    batch_content = f"""
@echo off
echo Input DXF: {input_dxf}
echo Output PDF: {output_pdf}
"{acad_exe_path}" /i "{input_dxf}" /s "{script_path}"
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
    batch_path = os.path.abspath("convert_dxf.bat")
    with open(batch_path, "w") as batch_file:
        batch_file.write(batch_content)
    return batch_path

def process_dxf_directory(acad_exe_path, input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")

    log_file = f"conversion_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Filename', 'Error'])
        
        for filename in os.listdir(input_dir):
            if filename.lower().endswith('.dxf'):
                input_path = os.path.join(input_dir, filename)
                output_filename = os.path.splitext(filename)[0] + '.pdf'
                output_path = os.path.join(output_dir, output_filename)
                
                logger.info(f"Converting {filename} to PDF...")
                error = convert_dxf_to_pdf(acad_exe_path, input_path, output_path)
                if error:
                    logger.error(f"Error converting {filename}: {error}")
                    csv_writer.writerow([filename, error])
                else:
                    logger.info(f"Converted {filename} to {output_filename}")

    logger.info("Conversion process completed.")

# Example usage
acad_exe_path = r"C:\CAD\Autodesk\AutoCAD 2022\accoreconsole.exe"
input_directory = r"Rerun PDFs directory2"
output_directory = r"C:\Users\U436445\OneDrive - Danfoss\Desktop\PDFsMissingB1_15k"

process_dxf_directory(acad_exe_path, input_directory, output_directory)
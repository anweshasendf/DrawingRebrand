import subprocess
import os

# PARAMS:
# Input folder
# Output folder
# Output version: ACAD9, ACAD10, ACAD12, ACAD14, ACAD2000, ACAD2004, ACAD2007, ACAD2010, ACAD2013, ACAD2018
# Output file type: DWG, DXF, DXB
# Recurse Input Folder: 0, 1
# Audit each file: 0, 1
# (Optional) Input files filter: *.DWG, *.DXF

TEIGHA_PATH = r"C:\Program Files\ODA\ODAFileConverter 25.5.0\ODAFileConverter.exe"
INPUT_FOLDER = r"DS_2\B_123_DXF_Out"  # Change this to  DXF input folder
OUTPUT_FOLDER = r"DS_2\B_123_DWG_Out"  # Change this to desired DWG output folder
OUTVER = "ACAD2018" 
OUTFORMAT = "DWG"  # Changed to DWG for the output format
RECURSIVE = "0"
AUDIT = "1"
INPUTFILTER = "*.DXF"  # Changed to filter DXF files

# Ensure output directory exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Command to run
cmd = [TEIGHA_PATH, INPUT_FOLDER, OUTPUT_FOLDER, OUTVER, OUTFORMAT, RECURSIVE, AUDIT, INPUTFILTER]


try:
    result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
    print("Conversion completed successfully.")
    print(f"Output: {result.stdout}")
except subprocess.CalledProcessError as e:
    print(f"Error during conversion: {e}")
    print(f"Error output: {e.stderr}")

# Print converted files
print("\nConverted files:")
for file in os.listdir(OUTPUT_FOLDER):
    if file.lower().endswith('.dwg'):
        print(file)
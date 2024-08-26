

import subprocess

# PARAMS:
# Input folder
# Output folder
# Output version: ACAD9, ACAD10, ACAD12, ACAD14, ACAD2000, ACAD2004, ACAD2007, ACAD20010, ACAD2013, ACAD2018
# Output file type: DWG, DXF, DXB
# Recurse Input Folder: 0, 1
# Audit each file: 0, 1
# (Optional) Input files filter: *.DWG, *.DXF

TEIGHA_PATH = r"C:\Program Files\ODA\ODAFileConverter 25.5.0\ODAFileConverter.exe"
INPUT_FOLDER = r"6000_DWG_In"
OUTPUT_FOLDER = r"6000_DXF_In"
OUTVER = "ACAD2018"
OUTFORMAT = "DXF"
RECURSIVE = "0"
AUDIT = "1"
INPUTFILTER = "*.DWG"

# Command to run
cmd = [TEIGHA_PATH, INPUT_FOLDER, OUTPUT_FOLDER, OUTVER, OUTFORMAT, RECURSIVE, AUDIT, INPUTFILTER]

# Run
subprocess.run(cmd, shell=True)
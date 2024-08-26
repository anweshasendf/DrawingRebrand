import pandas as pd
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons import odafc
import os
import shutil
from ezdxf.addons.dxf2code import entities_to_code, block_to_code
from ezdxf.addons import Importer
import re


def load_layout_names(layout_dir=r'AutoCAD_rebrand\danfoss_dxf_layouts'):
    """
    Loads the names of all DXF layout files in the specified directory.

    Parameters:
    layout_dir (str): The directory containing the layout DXF files.

    Returns:
    list: A list of layout file names in lowercase.
    """
    layout_names = []
    for root, dirs, files in os.walk(layout_dir):
        for file in files:
            if file.endswith('.dxf'):
                layout_names.append(file.lower())
    return layout_names


def process_entity(entity, layouts):
    """
    Processes a DXF entity to check for specific keywords and patterns, updating counts accordingly.

    Parameters:
    entity (DXFEntity): The DXF entity to process.
    layouts (list): A list of layout file names.

    Returns:
    tuple: A tuple containing counts for logo, division, text, and IP change.
    """
    logo = division = ip_change = text = 0
    name_lower = entity.dxf.name.lower() if hasattr(entity.dxf, 'name') else ""

    if entity.dxftype() == "INSERT":
        if 'title' in name_lower:
            print('logo1')
            division += 1
            logo += 1
            ip_change += 1
        for layout in layouts:
            if name_lower in layout:
                if 'mo' in name_lower or 'mfg-' in name_lower or 'gdjt-' in name_lower or 'berea' in name_lower:
                    print('logo2')
                    logo = 1
                    division = 1
                    ip_change = 1
                elif 'eaton_stamp' in name_lower:
                    print('logo3')
                    logo += 1
                elif 'eaton_ip' in name_lower:
                    ip_change += 1
                elif 'aqp_symbo' in name_lower or 'aeroquip-text' in name_lower:
                    print('logo4')
                    logo = 1
                    division = 1
                elif 'A$C642C39B3' in entity.dxf.name.upper() or 'A$C235B4AE9' in entity.dxf.name.upper():
                    print('logo5')
                    logo = 1
                    division = 1

    elif entity.dxftype() == "TEXT":
        text_lower = entity.dxf.text.lower()
        if 'danfoss' in text_lower:
            text += 1
        elif '16016' in text_lower:
            ip_change += 1

    elif entity.dxftype() == "MTEXT":
        text_lower = entity.text.lower()
        if 'danfoss' in text_lower:
            text += 1
        elif '16016' in entity.dxf.text.lower():
            ip_change += 1

    return logo, division, text, ip_change


def main():
    """
    Main function to process batches of DXF files, analyze them, and generate a report.

    The function iterates through specified batches of DXF files, processes each file to count occurrences of specific
    keywords and patterns, and saves the results in a CSV report.
    """
    base_dir = r'TestDXF_Out' #OutputDXFSMod
    batch_range = range(1, 5)
    report_df = pd.DataFrame(columns=['file', 'logo', 'division', 'text', 'ip_change'])
    layouts = load_layout_names()

    for batch in batch_range:
        modded_dir = base_dir.format(batch)
        for root, dirs, files in os.walk(modded_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    print("Processing: " + file_path)
                    doc = ezdxf.readfile(file_path)
                    logo = division = text = ip_change = 0

                    for entity in doc.entities:
                        l, d, t, i = process_entity(entity, layouts)
                        logo += l
                        division += d
                        text += t
                        ip_change += i

                    row = {
                        'file': file,
                        'logo': logo,
                        'division': division,
                        'text': text,
                        'ip_change': ip_change
                    }
                    report_df = report_df._append(row, ignore_index=True)
                    print("Row: " + str(row))
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    output_csv = r'AutoCAD_rebrand\report.csv'
    report_df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    main()
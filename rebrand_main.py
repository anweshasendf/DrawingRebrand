import os
import time

import ezdxf
import pandas as pd
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons import odafc
import os
import shutil
from ezdxf.addons.dxf2code import entities_to_code, block_to_code
from ezdxf.addons import Importer
import difflib
from fuzzywuzzy import process
import Levenshtein
import re


##################GLOBALS#######################3
eaton_ip =  r"CONFIDENTIAL AND PROPRIETARY NOTICE TO PERSONS RECEIVING THIS DRAWING AND/OR TECHNICAL INFORMATION THIS DOCUMENT, INCLUDING THE DRAWING AND INFORMATION CONTAINED THEREON, IS CONFIDENTIAL AND IS THE EXCLUSIVE PROPERTY OF EATON CORPORATION, MERELY ON LOAN AND SUBJECT TO RECALL BY EATON AT ANY TIME.   BY TAKING POSSESSION OF THIS DOCUMENT, THE RECIPIENT ACKNOWLEDGES AND AGREES THAT THIS DOCUMENT CANNOT BE USED IN ANY MANNER ADVERSE TO THE INTERESTS OF EATON AND THAT NO PORTION OF THIS DRAWING MAY BE COPIED OR OTHERWISE REPRODUCED WITHOUT THE PRIOR WRITTEN CONSENT OF EATON.  IN THE CASE OF CONFLICTING CONTRACTUAL PROVISIONS, THIS NOTICE SHALL GOVERN THE STATUS OF THIS DOCUMENT. {\W0.9; }© 2009 Eaton Corporation - All Rights Reserved"
eaton_ip_2 = r"\pxsm1,qc;{\H1.02x;EATON CORPORATION - CONFIDENTIAL AND PROPRIETARY NOTICE TO PERSONS RECEIVING THIS DOCUMENT AND/OR TECHNICAL INFORMATION\P\psm0.9,qj;\H0.96079x;THIS DOCUMENT, INCLUDING THE DRAWING AND INFORMATION CONTAINED THEREON, IS CONFIDENTIAL AND IS THE EXCLUSIVE PROPERTY OF EATON CORPORATION, AND IS MERELY ON LOAN AND SUBJECT TO RECALL BY EATON AT ANY TIME.  BY TAKING POSSESSION OF THIS DOCUMENT, THE RECIPIENT ACKNOWLEDGES AND AGREES THAT THIS DOCUMENT CANNOT BE USED IN ANY MANNER ADVERSE TO THE INTERESTS OF EATON, AND THAT NO PORTION OF THIS DOCUMENT MAY BE COPIED OR OTHERWISE REPRODUCED WITHOUT THE PRIOR WRITTEN CONSENT OF EATON.  IN THE CASE OF CONFLICTING CONTRACTUAL PROVISIONS, THIS NOTICE SHALL GOVERN THE STATUS OF THIS DOCUMENT.\H1.0204x;\W0.9;  \H0.98x;\W1;©Eaton Corporation - All Rights Reserved}"
eaton_ip_3 = r"CONFIDENTIAL AND PROPRIETARY NOTICE TO PERSONS RECEIVING THIS DRAWING AND/OR TECHNICAL INFORMATION THIS DOCUMENT, INCLUDING THE DRAWING AND INFORMATION CONTAINED THEREON, IS CONFIDENTIAL AND IS THE EXCLUSIVE PROPERTY OF EATON CORPORATION, MERELY ON LOAN AND SUBJECT TO RECALL BY EATON AT ANY TIME.   BY TAKING POSSESSION OF THIS DOCUMENT, THE RECIPIENT ACKNOWLEDGES AND AGREES THAT THIS DOCUMENT CANNOT BE USED IN ANY MANNER ADVERSE TO THE INTERESTS OF EATON AND THAT NO PORTION OF THIS DRAWING MAY BE COPIED OR OTHERWISE REPRODUCED WITHOUT THE PRIOR WRITTEN CONSENT OF EATON.  IN THE CASE OF CONFLICTING CONTRACTUAL PROVISIONS, THIS NOTICE SHALL GOVERN THE STATUS OF THIS DOCUMENT.  © 2009 Eaton Corporation - All Rights Reserved"
eaton_ip_4 = r"PROPERTY OF EATON CORPORATION"

danfoss_ip = r"THE REPRODUCTION, DISTRIBUTION, AND UTILIZATION OF THIS DOCUMENT AS WELL AS THE COMMUNICATION OF ITS CONTENTS TO OTHERS WITHOUT EXPLICIT AUTHORIZATION IS PROHIBITED. OFFENDERS WILL BE HELD LIABLE FOR THE PAYMENT OF DAMAGES. ALL RIGHTS RESERVED INTHE EVENT OF THE GRANT OF A PATENT, UTILITY MODEL OR DESIGN. (PER ISO 16016)"
aeroquip_ip_1 = r"THE INFORMATION DISCLOSED ON THIS DRAWING IS"
aeroquip_ip_2 = r"FOR PROCUREMENT OR MANUFACTURING"
aeroquip_ip_3 = r"DFARS"

report_df = pd.DataFrame()
danfoss_files = []
save_cnt =0


def split_by_words(text, parts=3):
    """
    Splits a given text into a specified number of parts, each containing a roughly equal number of words.

    Parameters:
    text (str): The text to be split.
    parts (int): The number of parts to split the text into. Default is 3.

    Returns:
    list: A list containing the text split into the specified number of parts.

    Example:
    >>> split_by_words("This is a sample text to be split into parts", 3)
    ['This is a', 'sample text to', 'be split into parts']
    """

    # Split the text into a list of words
    words = text.split()

    # Calculate the number of words per part
    words_per_part = len(words) // parts

    # Initialize the result list and the starting index
    result = []
    start = 0

    # Loop over the number of parts
    for i in range(parts):
        # Calculate the ending index for the current part
        end = start + words_per_part

        # If this is the last part, include all remaining words
        if i == parts - 1:
            result.append(' '.join(words[start:]))
        else:
            result.append(' '.join(words[start:end]))

        # Update the starting index for the next part
        start = end

    return result


def get_doc_info(file_path):
    """
    Extracts information from a DXF file and identifies specific keywords in various entities.

    Parameters:
    file_path (str): The path to the DXF file.

    Returns:
    list: A list containing extracted information in the format [manufacturer, digits_text, block_name, special_block_name].

    The list contains:
    - Manufacturer name (e.g., 'eaton', 'danfoss', 'aeroquip', 'obsolete')
    - Text containing a high percentage of digits
    - Block name containing 'title'
    - Special block name with specific keywords
    """

    # Read the DXF file
    doc = ezdxf.readfile(file_path)
    save_needed = False
    ret_arr = [''] * 4  # Initialize the return array with empty strings 0-company name, 1-cage_code, 2-block_name, 3-any other block to be replaces

    # Iterate through all entities in the document
    for entity in doc.entities:
        if entity.dxftype() == "INSERT":
            # Check for block names containing 'title'
            if "title" in entity.dxf.name.lower():
                block_name = entity.dxf.name
                ret_arr[2] = block_name
                block = doc.blocks.get(block_name)

                # Check for TEXT and MTEXT entities within the block
                for e in block:
                    if e.dxftype() == "TEXT":
                        num_digits = sum(c.isdigit() for c in e.dxf.text.lower())
                        if 'eaton' in e.dxf.text.lower():
                            ret_arr[0] = 'eaton'
                        elif 'danfoss' in e.dxf.text.lower() or '16016' in e.dxf.text.lower():
                            ret_arr[0] = 'danfoss'
                        elif 'aeroquip' in e.dxf.text.lower() and ret_arr[0] == '':
                            ret_arr[0] = 'aeroquip'
                        elif num_digits / len(e.dxf.text.lower()) > 0.5:
                            ret_arr[1] = e.dxf.text.lower()
                    elif e.dxftype() == "MTEXT":
                        if 'eaton' in e.text.lower():
                            ret_arr[0] = 'eaton'
                        elif 'danfoss' in e.text.lower() or '16016' in e.text.lower() and ret_arr[0] == '':
                            ret_arr[0] = 'danfoss'
                        elif 'aeroquip' in e.text.lower() and ret_arr[0] == '':
                            ret_arr[0] = 'aeroquip'

            # Check for other specific block names
            elif 'symbo_' in entity.dxf.name.lower() or 'aeroquip' in entity.dxf.name.lower() or 'MO_' in entity.dxf.name.lower() and \
                    ret_arr[2] == '':
                block_name = entity.dxf.name
                ret_arr[0] = 'aeroquip'
                ret_arr[2] = block_name
            elif ('mfg-jt' in entity.dxf.name.lower() or 'mfg-xz' in entity.dxf.name.lower()) and ret_arr[2] == '':
                block_name = entity.dxf.name
                ret_arr[0] = 'eaton'
                ret_arr[2] = block_name
            elif 'gdjt-' in entity.dxf.name.lower() and ret_arr[2] == '':
                block_name = entity.dxf.name
                ret_arr[0] = 'eaton'
                ret_arr[2] = block_name
            elif 'A$C235B4AE9'.lower() in entity.dxf.name.lower() or 'A$C642C39B3'.lower() in entity.dxf.name.lower():
                block_name = entity.dxf.name
                ret_arr[0] = 'eaton'
                ret_arr[2] = block_name
            elif 'eaton_berea' in entity.dxf.name.lower() and ret_arr[2] == '':
                block_name = entity.dxf.name
                ret_arr[0] = 'eaton'
                ret_arr[2] = block_name
            elif 'eaton_ip' in entity.dxf.name.lower():
                ret_arr[3] = entity.dxf.name
            elif 'eaton_stamp' in entity.dxf.name.lower():
                ret_arr[3] = entity.dxf.name

    # Iterate through all entities again to check for TEXT and MTEXT entities
    for entity in doc.entities:
        if entity.dxftype() == "TEXT":
            if 'eaton' in entity.dxf.text.lower() and ret_arr[0] != 'danfoss':
                ret_arr[0] = 'eaton'
            elif 'danfoss' in entity.dxf.text.lower() or '16016' in entity.dxf.text.lower() and not save_needed:
                ret_arr[0] = 'danfoss'
            elif 'aeroquip' in entity.dxf.text.lower() and ret_arr[0] == '':
                ret_arr[0] = 'aeroquip'
            elif 'obsolete' in entity.dxf.text.lower() and ret_arr[0] == '':
                ret_arr[0] = 'obsolete'
            elif aeroquip_ip_1.lower() in entity.dxf.text.lower():
                if ret_arr[0] == '':
                    ret_arr[0] = 'aeroquip'
                print("SPLIT AERO 1")
                save_needed = True
                entity.dxf.text = split_by_words(danfoss_ip)[0]
                entity.dxf.height = entity.dxf.height * 0.75
            elif aeroquip_ip_2.lower() in entity.dxf.text.lower():
                if ret_arr[0] == '':
                    ret_arr[0] = 'aeroquip'
                print("SPLIT AERO 2")
                save_needed = True
                entity.dxf.text = split_by_words(danfoss_ip)[1]
                entity.dxf.height = entity.dxf.height * 0.75
            elif aeroquip_ip_3.lower() in entity.dxf.text.lower():
                if ret_arr[0] =='':
                    ret_arr[0] = 'aeroquip'
                print("SPLIT AERO 3")
                save_needed = True
                entity.dxf.text = split_by_words(danfoss_ip)[2]
                entity.dxf.height = entity.dxf.height * 0.75
        elif entity.dxftype() == "MTEXT":
            #print(entity.text)
            if (eaton_ip.lower() in entity.text.lower() or
                    eaton_ip_2.lower() in entity.text.lower() or
                    eaton_ip_3.lower() in entity.dxf.text.lower() or
                  'PROPERTY OF EATON CORPORATION' in entity.text.upper()):
                ret_arr[0] = 'eaton'
                entity.text = danfoss_ip
                save_needed = True
                print("Modified MTEXT IP")
            if 'eaton' in entity.text.lower() and ret_arr[0] != 'danfoss':
                ret_arr[0] = 'eaton'
            elif ('danfoss' in entity.text.lower() or '16016' in entity.text.lower()) and not save_needed:
                ret_arr[0] = 'danfoss'
            elif 'aeroquip' in entity.text.lower() and ret_arr[0] == '':
                ret_arr[0] = 'aeroquip'
            elif 'obsolete' in entity.text.lower() and ret_arr[0] == '':
                ret_arr[0] = 'obsolete'


    # Save the document if modifications were made
    if save_needed:
        doc.saveas(file_path)

    return ret_arr


def get_df_layout(company_name, block_name, cage_code, layout_dir):
    """
    Finds the closest matching DXF file in a specified directory based on the provided search parameters.

    Parameters:
    company_name (str): The name of the company.
    block_name (str): The name of the block.
    cage_code (str): The CAGE code.
    layout_dir (str): The directory where the DXF files are located.

    Returns:
    str: The full path of the closest matching DXF file, or None if no DXF files are found.

    The function uses the Levenshtein distance to determine the closest match.
    """

    # Combine the search parameters into a single search string
    search_string = f"{block_name}_{company_name}_{cage_code}".lower()

    # List all files in the specified directory
    all_files = os.listdir(layout_dir)

    # Filter to include only .dxf files
    dxf_files = [file for file in all_files if file.endswith('.dxf')]

    # If no DXF files are found, return None
    if not dxf_files:
        return None

    # Initialize variables to track the closest match and its score
    closest_match = None
    highest_score = float('inf')

    # Iterate over the .dxf files to find the closest match using Levenshtein distance
    for file in dxf_files:
        score = Levenshtein.distance(search_string, file.lower())
        if score < highest_score:
            highest_score = score
            closest_match = file

    # Return the full path of the closest matching file
    return os.path.join(layout_dir, closest_match) if closest_match else None


def rebrand_dxf(src_dir, dest_dir, layout_dir):
    """
    Rebrands DXF files by replacing specific blocks based on the company name, block name, and cage code.

    Parameters:
    src_dir (str): The source directory containing the DXF files to be rebranded.
    dest_dir (str): The destination directory where the rebranded DXF files will be saved.
    layout_dir (str): The directory containing the layout DXF files used for rebranding.

    This function iterates through all DXF files in the source directory, identifies the company name, block name,
    and cage code, and replaces specific blocks with corresponding blocks from the layout directory.
    It saves the modified files in the destination directory and prints a summary of the processed files.
    """

    # Initialize counters for tracking the number of files processed and categorized
    non_modded_cnt = 0
    total_cnt = 0
    danfoss_cnt = 0
    modded_cnt = 0
    eaton_cnt = 0
    aeroquip_cnt = 0
    obsolete_cnt = 0

    # Iterate through all files in the source directory
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".dxf"):
                total_cnt += 1
                src_file_path = os.path.join(root, file)
                doc_info = get_doc_info(src_file_path)

                doc_info = get_doc_info(os.path.join(root, file))

                # Extract information from the document
                company_name = doc_info[0]
                cage_code = doc_info[1]
                block_name = doc_info[2]

                # Update counters based on the company name
                if company_name == 'eaton':
                    eaton_cnt += 1
                elif company_name == 'danfoss':
                    danfoss_cnt += 1
                elif company_name == 'aeroquip':
                    aeroquip_cnt += 1
                elif company_name == 'obsolete':
                    obsolete_cnt += 1

                # Read the target DXF file
                target_doc = ezdxf.readfile(os.path.join(root, file))
                print("File: " + file)
                print('Company: ' + company_name)
                print("Cage code: " + cage_code)
                print("Block name: " + block_name)

                # If the company is Danfoss, add the file to a list (not shown in the original function)
                if company_name.lower() == 'danfoss':
                    danfoss_files.append(os.path.join(root, file))
                    
                relative_path = os.path.relpath(root, src_dir)
                dest_file_path = os.path.join(dest_dir, relative_path, file)
                os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)

                # If the company name and block name are valid and not Danfoss, proceed with rebranding
                if company_name and company_name != 'danfoss' and block_name:
                    ip_note_block_changed = False

                    # Check if there is a special block to replace (e.g., IP block)
                    if doc_info[3]:
                        df_block_file = get_df_layout(company_name, doc_info[3], cage_code, layout_dir)
                        if df_block_file:
                            df_doc = ezdxf.readfile(df_block_file)
                            if 'ip' in df_block_file.lower():
                                print("IP block file: " + df_block_file)
                            elif 'stamp' in df_block_file.lower():
                                print("Stamp file: " + df_block_file)

                            # Import and replace the special block
                            importer = Importer(df_doc, target_doc)
                            target_doc.blocks.delete_block(doc_info[3], safe=False)
                            try:
                                importer.import_block(doc_info[3])
                            except Exception as e:
                                print("IP error occurred in double block replace")
                            importer.finalize()
                            ip_note_block_changed = True
                            target_doc.saveas(os.path.join(root, file))

                    # Get the layout file for the main block and replace it
                    df_block_file = get_df_layout(company_name, block_name, cage_code, layout_dir)
                    if df_block_file:
                        df_doc = ezdxf.readfile(df_block_file)
                        print("TEMPLATE file: " + df_block_file)
                        importer = Importer(df_doc, target_doc)
                        target_doc.blocks.delete_block(block_name, safe=False)
                        try:
                            importer.import_block(block_name)
                        except Exception as e:
                            print("LAYOUT BLOCK: " + block_name)
                            print(">" * 50)
                            continue
                        importer.finalize()

                        # Calculate the relative path and save the modified file
                        relative_path = os.path.relpath(root, src_dir)
                        dest_file_path = os.path.join(dest_dir, relative_path, file)
                        os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                        target_doc.saveas(dest_file_path)
                        modded_cnt += 1
                        print("Modified: " + dest_file_path)
                        print("_" * 50)
                    
                else:
                    shutil.copy2(src_file_path, dest_file_path)

                    non_modded_cnt += 1
                    print("_" * 50)

    # Print a summary of the processed files
    print("Total files: " + str(total_cnt))
    print("Danfoss files: " + str(danfoss_cnt))
    print("Modified count: " + str(modded_cnt))
    print("Non-modified count: " + str(non_modded_cnt - danfoss_cnt))


def main():
    """
    Main function to rebrand DXF files by replacing specific blocks based on company name, block name, and cage code.
    The function processes files from the input directory, modifies them using layout files, and saves the results in the output directory.
    It also measures and prints the total time taken for processing.
    """

    # Define the input, output, and layout directories
    input_dir = r'TestDXF_In' #Or OnlyDXF for 1st Try
    output_dir = r'TestDXF_Out'
    layout_dir = r'AutoCAD_rebrand\danfoss_dxf_layouts'

    # Count the number of files to be processed
    file_count = len([name for name in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, name))])
    print(f"Number of files to be processed: {file_count}")

    # Start the timer
    start = time.time()
    print("Started processing")

    # Call the rebrand_dxf function to process the files
    rebrand_dxf(input_dir, output_dir, layout_dir)

    # End the timer
    end = time.time()

    # Calculate the total time taken
    total_time = end - start

    # Print the results
    print(f"It took a total of {total_time:.2f} seconds to run this code.")
if __name__=="__main__":
    main()

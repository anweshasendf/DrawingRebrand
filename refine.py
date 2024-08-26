import pandas as pd
import matplotlib.pyplot as plt
import ezdxf
from ezdxf.addons import odafc
import os
import shutil
from ezdxf.addons.dxf2code import entities_to_code, block_to_code
from ezdxf.addons import Importer
import re

#####################GLOBALS#################################
output_dir = r'Beyond_97k_DXF_Out' #Was OutputDXFSMod
layout_dir = r'danfoss_dxf_layouts'


def replace_eaton_with_danfoss(text):
    """
    Replaces all occurrences of the word 'eaton' with 'danfoss' in a given text while preserving the case of the original word.

    Parameters:
    text (str): The input text in which the replacement will be performed.

    Returns:
    str: The modified text with 'eaton' replaced by 'danfoss' in the appropriate case.

    The function handles the following cases:
    - If 'eaton' is in uppercase, it is replaced with 'DANFOSS'.
    - If 'eaton' is in lowercase, it is replaced with 'danfoss'.
    - If 'eaton' is in title case, it is replaced with 'Danfoss'.
    - For mixed case or other cases, it defaults to 'danfoss'.
    """

    def case_sensitive_replace(match):
        """
        A helper function that determines the case of the matched word and returns 'danfoss' in the corresponding case.

        Parameters:
        match (re.Match): The match object containing the original word.

        Returns:
        str: The word 'danfoss' in the appropriate case.
        """
        original_word = match.group()
        if original_word.isupper():
            return 'DANFOSS'
        elif original_word.islower():
            return 'danfoss'
        elif original_word.istitle():
            return 'Danfoss'
        else:
            return 'danfoss'

    # Compile a regular expression pattern to match 'eaton' in a case-insensitive manner
    pattern = re.compile(r'eaton', re.IGNORECASE)

    # Use the sub method to replace all occurrences of 'eaton' with the result of case_sensitive_replace
    return pattern.sub(case_sensitive_replace, text)


def main():
    """
    Main function to process DXF files and replace occurrences of 'eaton' with 'danfoss' while preserving the case.
    The function iterates through all DXF files in the output directory, modifies the text, and saves the changes.
    """

    # Define the output directory
    output_dir = r'Beyond_97k_DXF_Out'

    # Iterate through all files in the output directory
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".dxf"):
                print("Processing file: " + os.path.join(root, file))
                save_needed = False
                doc = ezdxf.readfile(os.path.join(root, file))

                # Iterate through all entities in the DXF document
                for e in doc.entities:
                    if e.dxftype() == 'INSERT':
                        block_name = e.dxf.name
                        block = doc.blocks.get(block_name)

                        # Iterate through entities in the block
                        for entity in block:
                            if entity.dxftype() == "TEXT":
                                if 'eaton' in entity.dxf.text.lower():
                                    print("#changed")
                                    entity.dxf.text = replace_eaton_with_danfoss(entity.dxf.text)
                                    entity.dxf.height = entity.dxf.height * 0.75
                                    save_needed = True
                            elif entity.dxftype() == "MTEXT":
                                if 'eaton' in entity.text.lower():
                                    print("#changed")
                                    entity.text = replace_eaton_with_danfoss(entity.text)
                                    
                                    entity.dxf.char_height = entity.dxf.char_height * 0.75
                                    save_needed = True
                    elif e.dxftype() == "TEXT":
                        if 'eaton' in e.dxf.text.lower():
                            print("#changed")
                            e.dxf.text = replace_eaton_with_danfoss(e.dxf.text)
                            e.dxf.height = e.dxf.height * 0.75
                            save_needed = True
                    elif e.dxftype() == "MTEXT":
                        if 'eaton' in e.text.lower():
                            print("#changed")
                            e.text = replace_eaton_with_danfoss(e.text)
                            e.dxf.char_height = e.dxf.char_height * 0.75
                            save_needed = True

                # Save the modified document if changes were made
                if save_needed:
                    doc.saveas(os.path.join(root, file))


if __name__ == "__main__":
    main()
    
#Add non modified from prev too 
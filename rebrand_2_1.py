import os
import time
import traceback
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
from ezdxf.entities import DXFEntity
from ezdxf.entities.copy import CopyNotSupported
from ezdxf.math import Vec2, Vec3
from ezdxf.entities import DXFEntity, Text, MText, Line, Circle, Arc, Ellipse, Hatch, AttDef, Insert


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

ALLOWED_KEYWORDS = ['eaton', 'danfoss', 'aeroquip', 'obsolete', '16016', 'property of eaton corporation']
PROTECTED_BLOCKS = ["MFG-JT-通用"]  # Add other block names as needed
PROTECTED_PATTERNS = ["HRB", "OOTMO"]

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

def should_preserve_entity(entity):
    # Check if entity is in a protected block
    if hasattr(entity, 'block'):
        block = entity.block
        if callable(block):
            try:
                block = block()
            except:
                # If calling block() fails, we can't determine the block name
                block = None
        
        if block and hasattr(block, 'name'):
            if block.name in PROTECTED_BLOCKS:
                return True
    
    # Check if text matches protected patterns
    if entity.dxftype() in ["TEXT", "MTEXT"]:
        text = entity.dxf.text if entity.dxftype() == "TEXT" else entity.text
        if any(pattern in text for pattern in PROTECTED_PATTERNS):
            return True
    
    return False

def get_preserved_entities(doc):
    return [entity for entity in doc.entities if should_preserve_entity(entity)]

def restore_preserved_entities(doc, preserved_entities):
    for entity in preserved_entities:
        try:
            doc.modelspace().add_entity(entity.copy())
        except Exception as e:
            print(f"Error restoring entity: {e}")
            
            
def safe_entity_copy(entity, target_doc):
    try:
        return entity.copy()
    except AttributeError:
        entity_type = entity.dxftype()
        if entity_type == 'TEXT':
            dxfattribs = {
                'insert': getattr(entity, 'insert', Vec3(0, 0, 0)),
                'height': getattr(entity, 'height', 1.0),
                'text': getattr(entity, 'text', ''),
                'style': getattr(entity, 'style', 'Standard'),
                'layer': getattr(entity, 'layer', '0'),
                'color': getattr(entity, 'color', 256),
            }
            return Text.new(dxfattribs=dxfattribs, doc=target_doc)
        elif entity_type == 'MTEXT':
            dxfattribs = {
                'insert': getattr(entity, 'insert', Vec3(0, 0, 0)),
                'char_height': getattr(entity, 'char_height', 1.0),
                'width': getattr(entity, 'width', 100),
                'style': getattr(entity, 'style', 'Standard'),
                'layer': getattr(entity, 'layer', '0'),
                'color': getattr(entity, 'color', 256),
            }
            new_entity = MText.new(dxfattribs=dxfattribs, doc=target_doc)
            new_entity.text = getattr(entity, 'text', '')
            return new_entity
        elif entity_type == 'LINE':
            dxfattribs = {
                'start': getattr(entity, 'start', Vec3(0, 0, 0)),
                'end': getattr(entity, 'end', Vec3(1, 1, 0)),
                'layer': getattr(entity, 'layer', '0'),
                'color': getattr(entity, 'color', 256),
            }
            return Line.new(dxfattribs=dxfattribs, doc=target_doc)
        elif entity_type == 'CIRCLE':
            dxfattribs = {
                'center': getattr(entity, 'center', Vec3(0, 0, 0)),
                'radius': getattr(entity, 'radius', 1.0),
                'layer': getattr(entity, 'layer', '0'),
                'color': getattr(entity, 'color', 256),
            }
            return Circle.new(dxfattribs=dxfattribs, doc=target_doc)
        elif entity_type == 'ARC':
            dxfattribs = {
                'center': getattr(entity, 'center', Vec3(0, 0, 0)),
                'radius': getattr(entity, 'radius', 1.0),
                'start_angle': getattr(entity, 'start_angle', 0),
                'end_angle': getattr(entity, 'end_angle', 360),
                'layer': getattr(entity, 'layer', '0'),
                'color': getattr(entity, 'color', 256),
            }
            return Arc.new(dxfattribs=dxfattribs, doc=target_doc)
        elif entity_type == 'ELLIPSE':
            dxfattribs = {
                'center': getattr(entity, 'center', Vec3(0, 0, 0)),
                'major_axis': getattr(entity, 'major_axis', Vec3(1, 0, 0)),
                'ratio': getattr(entity, 'ratio', 0.5),
                'start_param': getattr(entity, 'start_param', 0),
                'end_param': getattr(entity, 'end_param', 6.28318530717959),
                'layer': getattr(entity, 'layer', '0'),
                'color': getattr(entity, 'color', 256),
            }
            return Ellipse.new(dxfattribs=dxfattribs, doc=target_doc)
        elif entity_type == 'HATCH':
            dxfattribs = {
                'pattern_name': getattr(entity, 'pattern_name', 'SOLID'),
                'color': getattr(entity, 'color', 256),
                'layer': getattr(entity, 'layer', '0'),
            }
            new_hatch = Hatch.new(dxfattribs=dxfattribs, doc=target_doc)
            # Copy paths if available
            if hasattr(entity, 'paths'):
                for path in entity.paths:
                    if hasattr(path, 'vertices'):
                        # PolylinePath
                        new_hatch.paths.add_polyline_path(path.vertices, is_closed=path.is_closed)
                    elif hasattr(path, 'edges'):
                        # EdgePath
                        edge_path = new_hatch.paths.add_edge_path()
                        for edge in path.edges:
                            if edge.EDGE_TYPE == 'LineEdge':
                                edge_path.add_line(edge.start, edge.end)
                            elif edge.EDGE_TYPE == 'ArcEdge':
                                edge_path.add_arc(edge.center, edge.radius, edge.start_angle, edge.end_angle)
                            elif edge.EDGE_TYPE == 'EllipseEdge':
                                edge_path.add_ellipse(edge.center, edge.major_axis, edge.ratio, edge.start_angle, edge.end_angle)
                            elif edge.EDGE_TYPE == 'SplineEdge':
                                edge_path.add_spline(edge.fit_points, edge.control_points, edge.knot_values, edge.weights, edge.degree)
            return new_hatch
        elif entity_type == 'INSERT':
            dxfattribs = {
                'name': getattr(entity, 'name', 'UNKNOWN'),
                'insert': getattr(entity, 'insert', Vec3(0, 0, 0)),
                'xscale': getattr(entity, 'xscale', 1),
                'yscale': getattr(entity, 'yscale', 1),
                'zscale': getattr(entity, 'zscale', 1),
                'rotation': getattr(entity, 'rotation', 0),
                'layer': getattr(entity, 'layer', '0'),
                'color': getattr(entity, 'color', 256),
            }
            return Insert.new(dxfattribs=dxfattribs, doc=target_doc)
        elif entity_type == 'ATTDEF':
            dxfattribs = {
                'insert': getattr(entity, 'insert', Vec3(0, 0, 0)),
                'height': getattr(entity, 'height', 1.0),
                'text': getattr(entity, 'text', ''),
                'tag': getattr(entity, 'tag', 'TAG'),
                'prompt': getattr(entity, 'prompt', ''),
                'style': getattr(entity, 'style', 'Standard'),
                'layer': getattr(entity, 'layer', '0'),
                'color': getattr(entity, 'color', 256),
            }
            return AttDef.new(dxfattribs=dxfattribs, doc=target_doc)
        else:
            print(f"Unsupported entity type: {entity_type}")
            return None

        
def split_block(block, split_x_coordinate):
    left_entities = []
    right_entities = []
    for entity in block:
        try:
            if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'insert'):
                if entity.dxf.insert.x < split_x_coordinate:
                    left_entities.append(entity)
                else:
                    right_entities.append(entity)
            elif hasattr(entity, 'get_points'):
                points = entity.get_points()
                if points and points[0].x < split_x_coordinate:
                    left_entities.append(entity)
                else:
                    right_entities.append(entity)
            else:
                # If we can't determine the position, add to right entities
                right_entities.append(entity)
        except Exception as e:
            print(f"Error processing entity in split_block: {e}")
            # If there's an error, add to right entities
            right_entities.append(entity)
    return left_entities, right_entities

def preserve_left_part_of_block(doc, block_name, split_x_coordinate):
    if block_name in doc.blocks:
        block = doc.blocks[block_name]
        left_entities, _ = split_block(block, split_x_coordinate)
        return left_entities
    return []

def get_entity_x_coordinate(entity):
    if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'insert'):
        return entity.dxf.insert.x
    elif hasattr(entity, 'dxf') and hasattr(entity.dxf, 'start'):
        return entity.dxf.start.x
    elif hasattr(entity, 'get_points'):
        points = entity.get_points()
        if points:
            return points[0].x
    elif hasattr(entity, 'dxf') and hasattr(entity.dxf, 'center'):
        return entity.dxf.center.x
    else:
        # If we can't determine the position, assume it's on the left side
        return 0


def get_entity_x_coordinate(entity):
    if hasattr(entity, 'dxf') and hasattr(entity.dxf, 'insert'):
        return entity.dxf.insert.x
    elif hasattr(entity, 'dxf') and hasattr(entity.dxf, 'start'):
        return entity.dxf.start.x
    elif hasattr(entity, 'get_points'):
        points = entity.get_points()
        if points:
            if isinstance(points[0], (Vec2, Vec3)):
                return points[0].x
            elif isinstance(points[0], tuple):
                return points[0][0]  # Assuming the first element of the tuple is the x-coordinate
    elif hasattr(entity, 'dxf') and hasattr(entity.dxf, 'center'):
        return entity.dxf.center.x
    else:
        # If we can't determine the position, assume it's on the left side
        return 0
    
def replace_block(target_doc, target_block_name, layout_doc, layout_block_name):
    print(f"Replacing block '{target_block_name}' with layout from '{layout_block_name}'")
    
    if target_block_name not in target_doc.blocks:
        print(f"Block '{target_block_name}' not found in target document")
        return False

    # Delete the existing block in the target document
    target_doc.blocks.delete_block(target_block_name, safe=False)
    print(f"Deleted existing block '{target_block_name}' from target document")

    # Import the block from the layout document
    importer = Importer(layout_doc, target_doc)
    try:
        importer.import_block(layout_block_name)
        importer.finalize()
        print(f"Imported block '{layout_block_name}' from layout document")
        return True
    except Exception as e:
        print(f"Error importing block '{layout_block_name}': {str(e)}")
        return False
    
def replace_right_part_of_block(target_block, layout_block, split_x_coordinate):
    # Preserve left side entities
    left_entities = [entity for entity in target_block if get_entity_x_coordinate(entity) < split_x_coordinate]
    
    # Clear the target block
    for entity in list(target_block):
        target_block.delete_entity(entity)
    
    # Add back the preserved left entities
    for entity in left_entities:
        new_entity = safe_entity_copy(entity, target_block.doc)
        if new_entity:
            target_block.add_entity(new_entity)
    
    # Add all entities from the layout block that are on the right side
    for entity in layout_block:
        x_coordinate = get_entity_x_coordinate(entity)
        if x_coordinate >= split_x_coordinate:
            new_entity = safe_entity_copy(entity, target_block.doc)
            if new_entity:
                target_block.add_entity(new_entity)

def get_block_data(block):
    """
    Extract attribute values and dynamic block properties from a block.
    """
    data = {}
    for entity in block:
        if entity.dxftype() == 'ATTRIB':
            data[entity.dxf.tag] = entity.dxf.text
    
    # Store dynamic block properties if any
    if hasattr(block, 'block'):  # Check if it's a BlockReference
        block_ref = block
    else:
        block_ref = block.block_reference

    if block_ref and hasattr(block_ref, 'get_attribs'):
        for attrib in block_ref.get_attribs():
            data[attrib.dxf.tag] = attrib.dxf.text

    return data

def set_block_data(block, data):
    """
    Set attribute values and dynamic block properties for a block.
    """
    for entity in block:
        if entity.dxftype() == 'ATTRIB' and entity.dxf.tag in data:
            entity.dxf.text = data[entity.dxf.tag]
    
    # Set dynamic block properties if any
    if hasattr(block, 'block'):  # Check if it's a BlockReference
        block_ref = block
    else:
        block_ref = block.block_reference

    if block_ref and hasattr(block_ref, 'get_attribs'):
        for attrib in block_ref.get_attribs():
            if attrib.dxf.tag in data:
                attrib.dxf.text = data[attrib.dxf.tag]


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
            
            text_lower = entity.dxf.text.lower()
            if any(keyword in text_lower for keyword in ALLOWED_KEYWORDS):
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
                text_lower = entity.text.lower()
                if any(keyword in text_lower for keyword in ALLOWED_KEYWORDS):

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
            else: 
                continue


    # Save the document if modifications were made
    if save_needed:
        doc.saveas(file_path)

    return ret_arr


def get_df_layout(company_name, block_name, cage_code, layout_dir, extra_layouts_dir, file_name): #Was none
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

    if file_name and file_name.startswith('1FG') and block_name == 'GDJT-通用':
         special_layout_dir = r'AutoCAD_rebrand\extralayouts'
         special_file = f"{block_name}.dxf"
         special_path = os.path.join(special_layout_dir, special_file)
         if os.path.exists(special_path):
             return special_path
 
    
    if file_name and file_name.startswith('00TM0') and block_name == 'MFG-JT-通用':
        special_file = f"{block_name}_{company_name}2.dxf"
        special_path = os.path.join(layout_dir, special_file)
        if os.path.exists(special_path):
            return special_path
        
        
    if (file_name.startswith('1JM') or file_name.startswith('1JH') or file_name.startswith('144')) and block_name == 'MFG-JT-通用不锈钢':
        special_file = "MFG-JT-通用不锈钢.dxf"
        special_path = os.path.join(extra_layouts_dir, special_file)
        if os.path.exists(special_path):
            return special_path

    if file_name.startswith('247'):
        special_file1 = "B-Eaton.dxf"
        special_file2 = "A$C642C39B3_eaton.dxf"
        special_path1 = os.path.join(layout_dir, special_file1)
        special_path2 = os.path.join(layout_dir, special_file2)
        result = []
        if os.path.exists(special_path1):
            result.append(special_path1)
        if os.path.exists(special_path2):
            result.append(special_path2)
        if result:
            return result
        else:
            print(f"Warning: No layout files found for 247 case. Searched for {special_file1} and {special_file2}")
            return None

        
    #"C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\CADRebrand\TestDXF_Out\00TM0-12.dxf"
    
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


# def rebrand_dxf(src_dir, dest_dir, layout_dir):
#     """
#     Rebrands DXF files by replacing specific blocks based on the company name, block name, and cage code.

#     Parameters:
#     src_dir (str): The source directory containing the DXF files to be rebranded.
#     dest_dir (str): The destination directory where the rebranded DXF files will be saved.
#     layout_dir (str): The directory containing the layout DXF files used for rebranding.

#     This function iterates through all DXF files in the source directory, identifies the company name, block name,
#     and cage code, and replaces specific blocks with corresponding blocks from the layout directory.
#     It saves the modified files in the destination directory and prints a summary of the processed files.
#     """

#     # Initialize counters for tracking the number of files processed and categorized
#     non_modded_cnt = 0
#     total_cnt = 0
#     danfoss_cnt = 0
#     modded_cnt = 0
#     eaton_cnt = 0
#     aeroquip_cnt = 0
#     obsolete_cnt = 0

#     # Iterate through all files in the source directory
#     for root, dirs, files in os.walk(src_dir):
#         for file in files:
#             if file.endswith(".dxf"):
#                 total_cnt += 1
#                 src_file_path = os.path.join(root, file)
#                 doc_info = get_doc_info(src_file_path)

#                 doc_info = get_doc_info(os.path.join(root, file))
                
                


#                 # Extract information from the document
#                 company_name = doc_info[0]
#                 cage_code = doc_info[1]
#                 block_name = doc_info[2]

#                 # Update counters based on the company name
#                 if company_name == 'eaton':
#                     eaton_cnt += 1
#                 elif company_name == 'danfoss':
#                     danfoss_cnt += 1
#                 elif company_name == 'aeroquip':
#                     aeroquip_cnt += 1
#                 elif company_name == 'obsolete':
#                     obsolete_cnt += 1
                    
#                 target_doc = ezdxf.readfile(src_file_path)
#                 original_entities = list(target_doc.entities)

#                 # Read the target DXF file
#                 target_doc = ezdxf.readfile(os.path.join(root, file))
#                 print("File: " + file)
#                 print('Company: ' + company_name)
#                 print("Cage code: " + cage_code)
#                 print("Block name: " + block_name)

#                 # If the company is Danfoss, add the file to a list (not shown in the original function)
#                 if company_name.lower() == 'danfoss':
#                     danfoss_files.append(os.path.join(root, file))
#                     danfoss_files.append(src_file_path)

                    
#                 relative_path = os.path.relpath(root, src_dir)
#                 dest_file_path = os.path.join(dest_dir, relative_path, file)
#                 os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)

#                 # If the company name and block name are valid and not Danfoss, proceed with rebranding
#                 if company_name and company_name != 'danfoss' and block_name:
#                     ip_note_block_changed = False

#                     # Check if there is a special block to replace (e.g., IP block)
#                     if doc_info[3]:
#                         df_block_file = get_df_layout(company_name, doc_info[3] or block_name, cage_code, layout_dir)
#                         if df_block_file:
#                             df_doc = ezdxf.readfile(df_block_file)
#                             print("TEMPLATE file: " + df_block_file)
#                             if 'ip' in df_block_file.lower():
#                                 print("IP block file: " + df_block_file)
#                             elif 'stamp' in df_block_file.lower():
#                                 print("Stamp file: " + df_block_file)
                                
                                
#                             original_block = target_doc.blocks[block_name]
#                             original_data = get_block_data(original_block)

#                             # Import and replace the special block
#                             importer = Importer(df_doc, target_doc)
#                             target_doc.blocks.delete_block(doc_info[3] or block_name, safe=False)
#                             try:
#                                 importer.import_block(doc_info[3])
#                             except Exception as e:
#                                 print("IP error occurred in double block replace")
#                             importer.finalize()
#                             ip_note_block_changed = True
#                             new_block = target_doc.blocks[block_name]
#                             set_block_data(new_block, original_data)
#                             target_doc.saveas(os.path.join(root, file))

#                     # Get the layout file for the main block and replace it
#                     df_block_file = get_df_layout(company_name, block_name, cage_code, layout_dir)
#                     if df_block_file:
#                         df_doc = ezdxf.readfile(df_block_file)
#                         print("TEMPLATE file: " + df_block_file)
#                         importer = Importer(df_doc, target_doc)
#                         target_doc.blocks.delete_block(block_name, safe=False)
#                         try:
#                             importer.import_block(block_name)
#                         except Exception as e:
#                             print("LAYOUT BLOCK: " + block_name)
#                             print(">" * 50)
#                             continue
#                         importer.finalize()

#                         # Calculate the relative path and save the modified file
#                         relative_path = os.path.relpath(root, src_dir)
#                         dest_file_path = os.path.join(dest_dir, relative_path, file)
#                         os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
#                         target_doc.saveas(dest_file_path)
#                         modded_cnt += 1
#                         print("Modified: " + dest_file_path)
#                         print("_" * 50)
                        
#                 current_entities = set(target_doc.entities)
#                 for entity in original_entities:
#                     if entity not in current_entities:
#                         # Check if it's a non-keyword entity
#                         try:
#                             if isinstance(entity, DXFEntity):
#                                 if entity.dxftype() in ["TEXT", "MTEXT"]:
#                                     text = entity.dxf.text if entity.dxftype() == "TEXT" else entity.text
#                                     if not any(keyword in text.lower() for keyword in ALLOWED_KEYWORDS):
#                                         # Create a copy of the entity and add it back to the document
#                                         new_entity = entity.copy()
#                                         target_doc.modelspace().add_entity(new_entity)
#                                 elif entity.dxftype() != "ACAD_PROXY_ENTITY":
#                                     # For non-text entities (except ACAD_PROXY_ENTITY), create a copy and add them back
#                                     new_entity = entity.copy()
#                                     target_doc.modelspace().add_entity(new_entity)
#                         except CopyNotSupported:
#                             print(f"Skipping entity {entity.dxftype()} as it doesn't support copying.")
#                             continue


#                 target_doc.saveas(dest_file_path)
#                 modded_cnt += 1
#                 print("Modified: " + dest_file_path)

#             else:
#                 shutil.copy2(src_file_path, dest_file_path)

#                 non_modded_cnt += 1
#                 print("_" * 50)
                    
                

#     # Print a summary of the processed files
#     print("Total files: " + str(total_cnt))
#     print("Danfoss files: " + str(danfoss_cnt))
#     print("Modified count: " + str(modded_cnt))
#     print("Non-modified count: " + str(non_modded_cnt - danfoss_cnt))



def rebrand_dxf(src_dir, dest_dir, layout_dir, extra_layouts_dir):
    non_modded_cnt = 0
    total_cnt = 0
    danfoss_cnt = 0
    modded_cnt = 0
    eaton_cnt = 0
    aeroquip_cnt = 0
    obsolete_cnt = 0
    non_modified_count = 0
    under_review_cnt = 0

    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".dxf"):
                total_cnt += 1
                src_file_path = os.path.join(root, file)
                doc_info = get_doc_info(src_file_path)

                company_name = doc_info[0]
                cage_code = doc_info[1]
                block_name = doc_info[2]
                
                relative_path = os.path.relpath(root, src_dir)
                dest_file_path = os.path.join(dest_dir, relative_path, file)
                os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                
                shutil.copy2(src_file_path, dest_file_path)
                print(f"Copied to output: {dest_file_path}")
                
                

                if company_name == 'eaton':
                    eaton_cnt += 1
                elif company_name == 'danfoss':
                    danfoss_cnt += 1
                    danfoss_files.append(src_file_path)
                    continue
                elif company_name == 'aeroquip':
                    aeroquip_cnt += 1
                elif company_name == 'obsolete':
                    obsolete_cnt += 1
                    
                relative_path = os.path.relpath(root, src_dir)
                dest_file_path = os.path.join(dest_dir, relative_path, file)
                os.makedirs(os.path.dirname(dest_file_path), exist_ok=True)
                
                shutil.copy2(src_file_path, dest_file_path)
                print(f"Copied to output: {dest_file_path}")

                print(f"File: {file}")
                print(f'Company: {company_name}')
                print(f"Cage code: {cage_code}")
                print(f"Block name: {block_name}")

                 # Read the target DXF file
                target_doc = ezdxf.readfile(os.path.join(root, file))
                target_doc = ezdxf.readfile(dest_file_path)

                
             
                # If the company is Danfoss, add the file to a list (not shown in the original function)
                if company_name.lower() == 'danfoss':
                    danfoss_files.append(os.path.join(root, file))
                    
                    
                special_case_processed = False
                    
                if file.startswith('00TM0') and block_name == 'MFG-JT-通用':
                    layout_filename = f"{block_name}_{company_name}2.dxf"
                    df_block_file = f"{block_name}_{company_name}2.dxf"
                elif file.startswith('247'):
                    layout_filename = "B-Eaton.dxf"
                    df_block_file = os.path.join(layout_dir, layout_filename)
                elif file.startswith(('1JM', '1JH')):
                    layout_filename = "MFG-JT-通用不锈钢.dxf"
                    df_block_file = os.path.join(extra_layouts_dir, layout_filename)
                else:
                    layout_filename = f"{block_name}_{company_name}.dxf"
                    f_block_file = f"{block_name}_{company_name}.dxf"
                    
                
                if file.startswith('247'):
                    print(f"Processing 247 file: {file}")
                    print("Blocks in the target document:")
                    for block in target_doc.blocks:
                        print(f"  - {block.name}")
                    
                    df_block_files = get_df_layout(company_name, block_name, cage_code, layout_dir, extra_layouts_dir, file)
                    print(f"Layout files returned by get_df_layout: {df_block_files}")

                    if isinstance(df_block_files, list):
                        for df_block_file in df_block_files:
                            if os.path.exists(df_block_file):
                                df_doc = ezdxf.readfile(df_block_file)
                                print(f"TEMPLATE file for 247: {df_block_file}")
                                try:
                                    block_name_to_replace = os.path.splitext(os.path.basename(df_block_file))[0]
                                    if block_name_to_replace.endswith('_eaton'):
                                        block_name_to_replace = block_name_to_replace[:-6]  # Remove '_eaton' suffix
                                    print(f"Attempting to replace '{block_name_to_replace}' block")
                                    success = replace_block(target_doc, block_name_to_replace, df_doc, block_name_to_replace)
                                    if success:
                                        print(f"Block '{block_name_to_replace}' replaced successfully")
                                    else:
                                        print(f"Failed to replace block '{block_name_to_replace}'")
                                except Exception as e:
                                    print(f"Error replacing block '{block_name_to_replace}' in 247 file {file}: {str(e)}")
                                    print(f"Traceback: {traceback.format_exc()}")
                        special_case_processed = True
                        target_doc.saveas(dest_file_path)
                        modded_cnt += 1
                    else:
                        print(f"Layout files not found for 247 file: {df_block_files}")

                

                

                # If the company name and block name are valid and not Danfoss, proceed with rebranding
                if not special_case_processed and company_name and company_name != 'danfoss' and block_name:
                    
                    
                    print(f"Blocks in {file}:")
                    for block in target_doc.blocks:
                        print(f"  - {block.name}")

                    # Debug: Print all layout files
                    print(f"Layout files in {layout_dir}:")
                    for layout_file in os.listdir(layout_dir):
                        print(f"  - {layout_file}")
                        
                        
                    ip_note_block_changed = False
                    df_block_file = get_df_layout(company_name, block_name, cage_code, layout_dir, extra_layouts_dir, file)
                    
                    if file.startswith("1QT-16"):
                        # Use a specific layout file for 1QT-16 files
                        df_block_file = os.path.join(layout_dir, "AutoCAD_rebrand\danfoss_dxf_layouts\GDJT-通用.dxf")
                    else:
                        # Use the regular layout file selection process
                        df_block_file = get_df_layout(company_name, block_name, cage_code, layout_dir, extra_layouts_dir, file)
                        
                    

                    # Check if there is a special block to replace (e.g., IP block)
                    if doc_info[3]:
                        df_block_file = get_df_layout(company_name, doc_info[3], cage_code, layout_dir,  extra_layouts_dir, file)
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
                    df_block_file = get_df_layout(company_name, block_name, cage_code, layout_dir, extra_layouts_dir, file)
                    if df_block_file:
                        df_doc = ezdxf.readfile(df_block_file)
                        print("TEMPLATE file: " + df_block_file)
                        
                        try:
                            replace_block(target_doc, block_name, df_doc, block_name)
                            
                            print(f"Block '{block_name}' replaced successfully")
                        except Exception as e:
                            print(f"Error replacing block '{block_name}': {str(e)}")
                            continue
                        
                        importer = Importer(df_doc, target_doc)
                        # target_doc.blocks.delete_block(block_name, safe=False)
                        # try:
                        #     importer.import_block(block_name)
                        # except Exception as e:
                        #     print("LAYOUT BLOCK: " + block_name)
                        #     print(">" * 50)
                        #     continue
                        # importer.finalize()
                        
                        if block_name in target_doc.blocks:
                            target_doc.blocks.delete_block(block_name, safe=False)
                        try:
                            importer.import_block(block_name)
                        except Exception as e:
                            print(f"Error importing block '{block_name}': {str(e)}")
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
                        print(f"Layout file not found:")
                        non_modified_count += 1
                       
                        shutil.copy2(src_file_path, dest_file_path)
                        print(f"Copied for review: {dest_file_path}")
                        continue
                    
                else:
                    non_modded_cnt += 1
                    print("_" * 50)
                    non_modified_count += 1
                    continue 
                
            

    # Print a summary of the processed files
    print("Total files: " + str(total_cnt))
    print("Danfoss files: " + str(danfoss_cnt))
    print("Modified count: " + str(modded_cnt))
    print("Non-modified count: " + str(non_modded_cnt - danfoss_cnt))
    print("Under Review count: " + str(total_cnt - (non_modded_cnt - danfoss_cnt + danfoss_cnt + modded_cnt)))

    
    if total_cnt != (danfoss_cnt + modded_cnt + under_review_cnt + (total_cnt - danfoss_cnt - modded_cnt - under_review_cnt)):
        print("Warning: File count mismatch")


def main():
    """
    Main function to rebrand DXF files by replacing specific blocks based on company name, block name, and cage code.
    The function processes files from the input directory, modifies them using layout files, and saves the results in the output directory.
    It also measures and prints the total time taken for processing.
    """

    # Define the input, output, and layout directories
    input_dir = r'Batch_6\B6_DXF_In' #Or OnlyDXF for 1st Try
    output_dir = r'Batch_6\B6_DXF_Out'
    layout_dir = r'danfoss_dxf_layouts'
    extra_layouts_dir = r'extralayouts'


    # Count the number of files to be processed
    file_count = len([name for name in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, name))])
    print(f"Number of files to be processed: {file_count}")

    # Start the timer
    start = time.time()
    print("Started processing")

    # Call the rebrand_dxf function to process the files
    rebrand_dxf(input_dir, output_dir, layout_dir, extra_layouts_dir)

    # End the timer
    end = time.time()

    # Calculate the total time taken
    total_time = end - start

    # Print the results
    print(f"It took a total of {total_time:.2f} seconds to run this code.")
if __name__=="__main__":
    main()

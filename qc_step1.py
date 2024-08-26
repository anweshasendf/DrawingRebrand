#Old QC=3
import ezdxf
import os
import csv
import logging
from collections import defaultdict
import concurrent.futures
import multiprocessing
import re
import subprocess
import time
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from skimage.metrics import structural_similarity as ssim
import io
import traceback 
from ezdxf.math import Vec2, Vec3,  Matrix44


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_layout_names(layout_dir=r'danfoss_dxf_layouts'):
    layout_names = []
    for root, dirs, files in os.walk(layout_dir):
        for file in files:
            if file.endswith('.dxf'):
                layout_names.append(file.lower())
    return layout_names

def is_danfoss_file(file_path):
    try:
        doc = ezdxf.readfile(file_path)
        for entity in doc.entities:
            if entity.dxftype() in ("TEXT", "MTEXT"):
                text = entity.dxf.text if entity.dxftype() == "TEXT" else entity.text
                if 'danfoss' in text.lower() or 'conveyance' in entity.dxf.text.lower() or '16016' in entity.dxf.text.lower(): #Was Text
                    return True
        return False
    except Exception:
        return False


def process_entity(entity, layouts):
    logo = division = ip_change = text = 0
    name_lower = entity.dxf.name.lower() if hasattr(entity.dxf, 'name') else ""

    if entity.dxftype() == "INSERT":
        if 'title' in name_lower:
            division += 1
            logo += 1
            ip_change += 1
        for layout in layouts:
            if name_lower in layout:
                if 'mo' in name_lower or 'mfg-' in name_lower or 'gdjt-' in name_lower or 'berea' in name_lower:
                    logo = 1
                    division = 1
                    ip_change = 1
                elif 'eaton_stamp' in name_lower:
                    logo += 1
                elif 'eaton_ip' in name_lower:
                    ip_change += 1
                elif 'aqp_symbo' in name_lower or 'aeroquip-text' in name_lower:
                    logo = 1
                    division = 1
                elif 'A$C642C39B3' in entity.dxf.name.upper() or 'A$C235B4AE9' in entity.dxf.name.upper():
                    logo = 1
                    division = 1

    elif entity.dxftype() in ["TEXT", "MTEXT"]:
        text_lower = entity.dxf.text.lower() if entity.dxftype() == "TEXT" else entity.text.lower()
        if 'danfoss' in text_lower or 'danfoss' in entity.dxf.text.lower():
            text += 1
        elif '16016' in text_lower:
            ip_change += 1

    return logo, division, text, ip_change

def deep_parse_dxf(doc):
    entities = defaultdict(list)
    for entity in doc.modelspace():
        entity_data = parse_entity(entity)
        entities[entity.dxftype()].append(entity_data)
    return dict(entities)

def parse_entity(entity):
    entity_data = {
        'type': entity.dxftype(),
        'handle': entity.dxf.handle,
        'layer': entity.dxf.layer,
        'attributes': dict(entity.dxfattribs())
    }
    if entity.dxftype() == 'INSERT':
        entity_data['block'] = [parse_entity(e) for e in entity.block()]
    elif entity.dxftype() in ['TEXT', 'MTEXT']:
        entity_data['text'] = entity.dxf.text if entity.dxftype() == 'TEXT' else entity.text
    return entity_data

def load_dxf_elements(file_path):
    doc = ezdxf.readfile(file_path)
    return {
        'metadata': doc.ezdxf_metadata(),
        'entities': deep_parse_dxf(doc)
    }

def compare_entities(original, modified, ideal):
    changes = []
    all_types = set(original.keys()) | set(modified.keys()) | set(ideal.keys())
    
    for entity_type in all_types:
        orig_entities = original.get(entity_type, [])
        mod_entities = modified.get(entity_type, [])
        ideal_entities = ideal.get(entity_type, [])
        
        if len(mod_entities) != len(ideal_entities):
            changes.append(f"Number of {entity_type} entities is incorrect. Expected: {len(ideal_entities)}, Found: {len(mod_entities)}")
        
        for orig, mod, ideal in zip(orig_entities, mod_entities, ideal_entities):
            if mod != ideal:
                changes.append(f"{entity_type} entity (handle {mod['handle']}) is not correctly modified")
                if entity_type in ['TEXT', 'MTEXT']:
                    changes.append(f"  Expected text: '{ideal['text']}', Found: '{mod['text']}'")
            elif mod != orig:
                changes.append(f"{entity_type} entity (handle {mod['handle']}) was correctly modified")
    
    return changes

def compare_metadata(original, modified):
    changes = []
    attributes = ['created', 'updated', 'version', 'app_name', 'comments']
    
    for attr in attributes:
        orig_value = getattr(original, attr, None)
        mod_value = getattr(modified, attr, None)
        
        if orig_value != mod_value:
            changes.append(f"Changed metadata: {attr} from {orig_value} to {mod_value}")
    
    return changes

def compare_file_size(original_file, modified_file):
    original_size = os.path.getsize(original_file)
    modified_size = os.path.getsize(modified_file)
    size_change = abs(modified_size - original_size) / original_size
    
    if size_change > 0.15:
        return f"File size changed by more than 15%: {original_size} bytes to {modified_size} bytes"
    return None

def log_block_changes(original_file, modified_file):
    try:
        original_doc = ezdxf.readfile(original_file)
        modified_doc = ezdxf.readfile(modified_file)

        original_blocks = set(block.name for block in original_doc.blocks)
        modified_blocks = set(block.name for block in modified_doc.blocks)

        added_blocks = modified_blocks - original_blocks
        removed_blocks = original_blocks - modified_blocks
        common_blocks = original_blocks.intersection(modified_blocks)

        changes = []
        
        


        if added_blocks:
            changes.append(f"Added blocks: {', '.join(added_blocks)}")
        if removed_blocks:
            changes.append(f"Removed blocks: {', '.join(removed_blocks)}")

        for block_name in common_blocks:
            original_block = original_doc.blocks[block_name]
            modified_block = modified_doc.blocks[block_name]

            original_entities = len(list(original_block))
            modified_entities = len(list(modified_block))

            if original_entities != modified_entities:
                changes.append(f"Block '{block_name}' changed: {original_entities} -> {modified_entities} entities")

        return "; ".join(changes) if changes else "No significant block changes detected"

    except Exception as e:
        return f"Error comparing blocks: {str(e)}"

from pdf2image import convert_from_path

def convert_dxf_to_image(dxf_path, output_format='png'):
    try:
        # Path to your AutoCAD shortcut
        acad_shortcut = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\AutoCAD Mechanical 2022 - English\AutoCAD 2022 - English - AutoCAD Mechanical.lnk"
        
        # Create output paths
        output_dir = os.path.dirname(dxf_path)
        base_name = os.path.splitext(os.path.basename(dxf_path))[0]
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")
        png_path = os.path.join(output_dir, f"{base_name}.png")

        # Create AutoCAD script
        script_content = f"""
(command "_OPEN" "{dxf_path}")
(command "_ZOOM" "E")
(command "_-PLOT"
    "Y"           ; Detailed plot configuration
    ""            ; Layout name (empty for Model space)
    "DWG To PDF.pc3"  ; Plotter name
    "ISO full bleed A3 (420.00 x 297.00 MM)"  ; Paper size
    "Millimeters" ; Paper units
    "Landscape"   ; Paper orientation
    "N"           ; Plot upside down
    "E"           ; Plot area: Extents
    "F"           ; Plot scale: Fit
    "C"           ; Plot offset: Center
    "Y"           ; Plot style table
    "acad.ctb"    ; Plot style table name
    "Y"           ; Plot with plot styles
    "Y"           ; Plot with lineweights
    "N"           ; Plot with transparency
    "N"           ; Plot stamp on
    "{pdf_path}"  ; File name
    "N"           ; Save changes to page setup
    "Y"           ; Proceed with plot
)
(command "_CLOSE" "N")
(vl-exit)
"""

        # Write script to file
        script_path = os.path.join(output_dir, f"{base_name}_export_script.scr")
        with open(script_path, 'w') as f:
            f.write(script_content)

        # Run AutoCAD with the script
        cmd = f'start "" "{acad_shortcut}" /b "{script_path}"'
        subprocess.Popen(cmd, shell=True)

        # Wait for the PDF file to be created (with timeout)
        timeout = 60  # seconds
        while timeout > 0 and not os.path.exists(pdf_path):
            time.sleep(1)
            timeout -= 1

        if not os.path.exists(pdf_path):
            raise Exception("PDF export timed out")

        # Convert PDF to PNG
        images = convert_from_path(pdf_path)
        images[0].save(png_path, 'PNG')

        # Clean up temporary PDF file
        os.remove(pdf_path)

        return png_path

    except Exception as e:
        print(f"Error converting {dxf_path}: {str(e)}")
        return None
    
def create_autocad_script(input_dir, output_dir):
    input_dir_str = str(input_dir).replace("\\", "\\\\")
    output_dir_str = str(output_dir).replace("\\", "\\\\")
    
    script_content = f"""
(setvar "FILEDIA" 0)
(setvar "CMDDIA" 0)
(setq file_list (vl-remove nil (append (vl-directory-files "{input_dir_str}" "*.dwg" 1) (vl-directory-files "{input_dir_str}" "*.dxf" 1))))
(princ (strcat "\\nFound " (itoa (length file_list)) " DWG/DXF files\\n"))
(foreach file file_list
    (setq file_path (strcat "{input_dir_str}\\\\" file))
    (setq pdf_path (strcat "{output_dir_str}\\\\" (vl-filename-base file) ".pdf"))
    (princ (strcat "Processing: " file "\\n"))
    (command "_OPEN" file_path)
    (if (= (getvar "DWGNAME") nil)
        (princ (strcat "Error opening file: " file "\\n"))
        (progn
            (command "_PLOT"
                "_Y"
                ""
                "DWG To PDF.pc3"
                "ISO full bleed A3 (420.00 x 297.00 MM)"
                "_Millimeters"
                "_Landscape"
                "_No"
                "_Extents"
                "_Fit"
                "0,0"
                "_Yes"
                "_Yes"
                pdf_path
                "_Yes"
            )
            (if (not (findfile pdf_path))
                (princ (strcat "Error creating PDF: " file "\\n"))
                (princ (strcat "Successfully created PDF: " file "\\n"))
            )
        )
    )
    (command "_CLOSE" "_N")
)
(princ "Script completed\\n")
(princ)
(quit)
"""

    script_path = output_dir / "batch_plot.scr"
    with open(script_path, "w") as f:
        f.write(script_content)
    print(f"Created AutoCAD script: {script_path}")
    return script_path

def run_autocad_script(script_path):
    acad_shortcut = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\AutoCAD Mechanical 2022 - English\AutoCAD 2022 - English - AutoCAD Mechanical.lnk"
    cmd = f'start "" "{acad_shortcut}" /b "{script_path}"'
    try:
        print(f"Running AutoCAD script: {cmd}")
        subprocess.run(cmd, shell=True, check=True)
        print("Waiting for AutoCAD to finish...")
        time.sleep(60)  # Wait for 60 seconds, adjust if needed
        print("Finished waiting for AutoCAD")
    except subprocess.CalledProcessError as e:
        print(f"Error running AutoCAD script: {e}")
        
def convert_pdf_to_image(pdf_path, output_dir):
    try:
        images = convert_from_path(pdf_path)
        if images:
            image_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(pdf_path))[0]}.png")
            images[0].save(image_path, 'PNG')
            return image_path
        else:
            print(f"No images extracted from PDF: {pdf_path}")
            return None
    except Exception as e:
        print(f"Error converting PDF to image: {pdf_path}")
        print(f"Error details: {str(e)}")
        return None

import cv2
import numpy as np

def compare_images(image1_path, image2_path):
    # Read images
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)

    # Convert images to grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Compute the absolute difference between the images
    diff = cv2.absdiff(gray1, gray2)

    # Threshold the difference image
    thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)[1]

    # Find contours in the thresholded image
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create a copy of the original image to draw on
    result = img2.copy()

    # Draw circles around the differences
    for contour in contours:
        if cv2.contourArea(contour) > 100:  # Adjust this threshold as needed
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.circle(result, (x + w // 2, y + h // 2), max(w, h) // 2, (0, 0, 255), 2)

    # Calculate similarity (inverse of normalized difference)
    similarity = 1 - (np.sum(diff) / (255 * diff.size))

    return similarity, result


def get_hatch_bbox(hatch):
    bbox_min = None
    bbox_max = None

    for path in hatch.paths:
        if hasattr(path, 'vertices'):
            # PolylinePath
            for vertex in path.vertices:
                point = Vec3(vertex)
                if bbox_min is None:
                    bbox_min = bbox_max = point
                else:
                    bbox_min = Vec3(min(bbox_min.x, point.x),
                                    min(bbox_min.y, point.y),
                                    min(bbox_min.z, point.z))
                    bbox_max = Vec3(max(bbox_max.x, point.x),
                                    max(bbox_max.y, point.y),
                                    max(bbox_max.z, point.z))
        elif hasattr(path, 'edges'):
            # EdgePath
            for edge in path.edges:
                if edge.EDGE_TYPE == 'LineEdge':
                    points = [edge.start, edge.end]
                elif edge.EDGE_TYPE == 'ArcEdge':
                    points = [edge.center, edge.start_point, edge.end_point]
                elif edge.EDGE_TYPE == 'EllipseEdge':
                    points = [edge.center, edge.start_point, edge.end_point]
                elif edge.EDGE_TYPE == 'SplineEdge':
                    points = edge.control_points
                else:
                    continue

                for point in points:
                    point = Vec3(point)
                    if bbox_min is None:
                        bbox_min = bbox_max = point
                    else:
                        bbox_min = Vec3(min(bbox_min.x, point.x),
                                        min(bbox_min.y, point.y),
                                        min(bbox_min.z, point.z))
                        bbox_max = Vec3(max(bbox_max.x, point.x),
                                        max(bbox_max.y, point.y),
                                        max(bbox_max.z, point.z))

    return (bbox_min, bbox_max) if bbox_min is not None else None

def get_insert_bbox(insert):
    block = insert.block()
    if block is None:
        return None

    bbox_min = None
    bbox_max = None

    # Get insert's properties
    insert_point = Vec3(insert.dxf.insert)
    x_scale = insert.dxf.xscale
    y_scale = insert.dxf.yscale
    rotation = insert.dxf.rotation

    # Create transformation matrix
    m = Matrix44.chain(
        Matrix44.scale(x_scale, y_scale, 1),
        Matrix44.z_rotate(rotation),
        Matrix44.translate(insert_point.x, insert_point.y, insert_point.z)
    )

    for entity in block:
        if hasattr(entity, 'dxf'):
            if hasattr(entity.dxf, 'insert'):
                point = Vec3(entity.dxf.insert)
            elif hasattr(entity.dxf, 'start'):
                point = Vec3(entity.dxf.start)
            else:
                continue

            # Transform the point
            transformed_point = m.transform(point)

            if bbox_min is None:
                bbox_min = bbox_max = transformed_point
            else:
                bbox_min = Vec3(min(bbox_min.x, transformed_point.x),
                                min(bbox_min.y, transformed_point.y),
                                min(bbox_min.z, transformed_point.z))
                bbox_max = Vec3(max(bbox_max.x, transformed_point.x),
                                max(bbox_max.y, transformed_point.y),
                                max(bbox_max.z, transformed_point.z))

    if bbox_min is None or bbox_max is None:
        return None

    return (bbox_min, bbox_max)

def perform_extra_checks(original_doc, modified_doc):
    extra_checks = []

    # Check 1: 'eaton' word should not be visible anywhere in the drawings
    eaton_count = 0
    for entity in modified_doc.entities:
        if entity.dxftype() in ("TEXT", "MTEXT"):
            text = entity.dxf.text if entity.dxftype() == "TEXT" else entity.text
            eaton_count += text.lower().count('eaton')
    if eaton_count > 0:
        extra_checks.append(f"Found {eaton_count} instances of 'eaton' in the drawing")

    # Check 2: All instances of text and mtext should be within the line or title block / block name insert entities
    block_refs = list(modified_doc.query('INSERT'))
    text_outside_blocks = 0
    for entity in modified_doc.entities:
        if entity.dxftype() in ("TEXT", "MTEXT"):
            if not is_mtext_inside_blocks(entity, block_refs):
                text_outside_blocks += 1

    if text_outside_blocks > 100:
        extra_checks.append(f"Found {text_outside_blocks} text entities outside of blocks")

    # Check 3: Number of entities should not reduce from original number of entities
    original_entity_count = len(list(original_doc.entities))
    modified_entity_count = len(list(modified_doc.entities))
    if modified_entity_count < original_entity_count:
        extra_checks.append(f"Entity count reduced: Original {original_entity_count}, Modified {modified_entity_count}")
        
     # Check 4: Hatch entities outside the title block
    title_block = None
    for block_ref in block_refs:
        block_name = block_ref.dxf.name.lower()
        if ('title' in block_name or 
            'symbo_' in block_name or 
            'aeroquip' in block_name or 
            'MO_' in block_name or
            'mfg-jt' in block_name or 
            'mfg-xz' in block_name or
            'gdjt-' in block_name or
            'A$C235B4AE9'.lower() in block_name or 
            'A$C642C39B3'.lower() in block_name or
            'eaton_berea' in block_name):
            title_block = block_ref
            break

    if title_block:
        title_block_bbox = get_insert_bbox(title_block)
        if title_block_bbox:
            hatch_outside_title_block = 0

            for entity in modified_doc.entities:
                if entity.dxftype() == 'HATCH':
                    hatch_bbox = get_hatch_bbox(entity)
                    if hatch_bbox:
                        if not (title_block_bbox[0].x <= hatch_bbox[0].x <= title_block_bbox[1].x and
                                title_block_bbox[0].y <= hatch_bbox[0].y <= title_block_bbox[1].y):
                            hatch_outside_title_block += 1

            if hatch_outside_title_block > 4:
                extra_checks.append(f"Found {hatch_outside_title_block} hatch entities outside the title block")
        else:
            extra_checks.append("Unable to determine title block bounding box")
    else:
        extra_checks.append("Title block not found")


    return "; ".join(extra_checks) if extra_checks else "All extra checks passed"

def is_mtext_inside_blocks(mtext, block_refs):
    for block_ref in block_refs:
        block = block_ref.block()
        
        # Get all entities in the block
        entities = list(block)
        
        if not entities:
            continue
        
        # Initialize min and max coordinates
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        # Find the bounding box of all entities in the block
        for entity in entities:
            if hasattr(entity, 'dxf'):
                if hasattr(entity.dxf, 'insert'):
                    min_x = min(min_x, entity.dxf.insert.x)
                    min_y = min(min_y, entity.dxf.insert.y)
                    max_x = max(max_x, entity.dxf.insert.x)
                    max_y = max(max_y, entity.dxf.insert.y)
                elif hasattr(entity.dxf, 'start'):
                    min_x = min(min_x, entity.dxf.start.x, entity.dxf.end.x)
                    min_y = min(min_y, entity.dxf.start.y, entity.dxf.end.y)
                    max_x = max(max_x, entity.dxf.start.x, entity.dxf.end.x)
                    max_y = max(max_y, entity.dxf.start.y, entity.dxf.end.y)
        
        # Check if the MText is inside the block's bounding box
        if (min_x <= mtext.dxf.insert.x <= max_x and min_y <= mtext.dxf.insert.y <= max_y):
            return True
    
    return False

def process_file(args):
    filename, original_dir, modified_dir, ideal_dir, layouts, output_dir, original_dwg_dir, modified_dwg_dir, file_counter = args

    original_file = os.path.join(original_dir, filename)
    modified_file = os.path.join(modified_dir, filename)

    if not filename.lower().endswith(('.dwg', '.dxf')):
        print(f"Skipping non-DWG/DXF file: {filename}")
        return {
            'filename': filename,
            'logo': 0,
            'division': 0,
            'text': 0,
            'ip_change': 0,
            'comments': "Not a DWG or DXF file",
            'block_changes': '',
            #'similarity': '',
            'extra_checks': ''
        }

    if not os.path.exists(modified_file):
        print(f"Modified file not found: {modified_file}")
        return {
            'filename': filename,
            'logo': 0,
            'division': 0,
            'text': 0,
            'ip_change': 0,
            'comments': "Modified file not found",
            'block_changes': '',
            #'similarity': '',
            'extra_checks': ''
        }
        
    if not os.path.exists(modified_file):
        if is_danfoss_file(original_file):
            return {
                'filename': filename,
                'logo': 0,
                'division': 0,
                'text': 0,
                'ip_change': 0,
                'comments': "Danfoss file detected",
                'block_changes': '',
                'extra_checks': ''
            }
        else:
            return {
                'filename': filename,
                'logo': 0,
                'division': 0,
                'text': 0,
                'ip_change': 0,
                'comments': "Modified file not found",
                'block_changes': '',
                'extra_checks': ''
            }

    try:
        original_doc = ezdxf.readfile(original_file)
        modified_doc = ezdxf.readfile(modified_file)
        
        logo = division = text = ip_change = 0

        for entity in modified_doc.entities:
            l, d, t, i = process_entity(entity, layouts)
            logo += l
            division += d
            text += t
            ip_change += i

        original_elements = load_dxf_elements(original_file)
        modified_elements = load_dxf_elements(modified_file)
        
        size_change = compare_file_size(original_file, modified_file)
        metadata_changes = compare_metadata(original_elements['metadata'], modified_elements['metadata'])
        entity_changes = compare_entities(original_elements['entities'], modified_elements['entities'], modified_elements['entities'])
        block_changes = log_block_changes(original_file, modified_file)

        comments = []
        if size_change:
            comments.append(size_change)
        comments.extend(metadata_changes)
        comments.extend(entity_changes)
        
        extra_checks = perform_extra_checks(original_doc, modified_doc)

        result = "Unmodified / Review"
        if "Danfoss file detected" in comments:
            result = "Danfoss File"
        elif extra_checks == "All extra checks passed" and "File size changed by more than 15%" in comments:
            result = "Modified"
        elif "Send to Review" in comments or "Aeroquip file detected" in comments:
            result = "Unmodified / Review"
        else:
            result = "Unmodified / Review"  # Default case

        return {
            'filename': filename,
            'logo': logo,
            'division': division,
            'text': text,
            'ip_change': ip_change,
            'comments': '; '.join(comments) if comments else "No significant changes detected",
            'block_changes': block_changes,
            'extra_checks': extra_checks,
            'result': result
        }

    except Exception as e:
        print(f"Error processing file {filename}: {str(e)}")
        print(traceback.format_exc())
        return {
            'filename': filename,
            'logo': 0,
            'division': 0,
            'text': 0,
            'ip_change': 0,
            'comments': f"Error processing file: {str(e)}",
            'block_changes': '',
            'extra_checks': 'Error performing extra checks',
            'result': 'Unmodified / Review'
        }
        
def compare_multiple_files(original_dir, modified_dir, ideal_dir, output_dir, log_file, original_dwg_dir, modified_dwg_dir):
    
    
    
    
    original_files = set(os.listdir(original_dir))
    modified_files = set(os.listdir(modified_dir))
    layouts = load_layout_names()
    
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'logo', 'division', 'text', 'ip_change', 'comments', 'block_changes', 'extra_checks', 'result']

        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csvwriter.writeheader()

        with concurrent.futures.ProcessPoolExecutor() as executor:
            args_list = [(filename, original_dir, modified_dir, ideal_dir, layouts, output_dir, original_dwg_dir, modified_dwg_dir, i+1) for i, filename in enumerate(original_files)]
            results = executor.map(process_file, args_list)

            for result in results:
                if result['comments'] != "Not a DWG or DXF file":
                    csvwriter.writerow(result)

    print(f"Results written to {log_file}")

def main():
    original_dir = Path('Beyond_97k_DXF_In').resolve()
    modified_dir = Path('Beyond_97k_DXF_Out').resolve()
    ideal_dir = Path('IdealDXF').resolve()
    output_dir = Path('ComparisonOutput').resolve()
    original_dwg_dir = Path('Beyond_97k').resolve() 
    modified_dwg_dir = Path('Beyond_97k_DWG_Out').resolve()  

    log_file = os.path.join(output_dir, 'comprehensive_quality_check_run_test_batch_beyond97k.csv')

    compare_multiple_files(original_dir, modified_dir, ideal_dir, output_dir, log_file, original_dwg_dir, modified_dwg_dir)
if __name__ == '__main__':
    multiprocessing.freeze_support() 
    main()
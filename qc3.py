import ezdxf
import os
import csv
import logging
from collections import defaultdict
import concurrent.futures
import multiprocessing
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_layout_names(layout_dir=r'AutoCAD_rebrand\danfoss_dxf_layouts'):
    layout_names = []
    for root, dirs, files in os.walk(layout_dir):
        for file in files:
            if file.endswith('.dxf'):
                layout_names.append(file.lower())
    return layout_names

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
        if 'danfoss' in text_lower:
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

def process_file(args):
    filename, original_dir, modified_dir, ideal_dir, layouts = args
    original_file = os.path.join(original_dir, filename)
    modified_file = os.path.join(modified_dir, filename)

    if not os.path.exists(modified_file):
        return {
            'filename': filename,
            'logo': 0,
            'division': 0,
            'text': 0,
            'ip_change': 0,
            'comments': "Danfoss file (Modified file not found)"
        }

    try:
        doc = ezdxf.readfile(modified_file)
        logo = division = text = ip_change = 0

        for entity in doc.entities:
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

        comments = []
        if size_change:
            comments.append(size_change)
        comments.extend(metadata_changes)
        comments.extend(entity_changes)

        return {
            'filename': filename,
            'logo': logo,
            'division': division,
            'text': text,
            'ip_change': ip_change,
            'comments': '; '.join(comments) if comments else "No significant changes detected"
        }

    except Exception as e:
        return {
            'filename': filename,
            'logo': 0,
            'division': 0,
            'text': 0,
            'ip_change': 0,
            'comments': f"Error processing file: {str(e)}"
        }

def compare_multiple_files(original_dir, modified_dir, ideal_dir, log_file):
    original_files = set(os.listdir(original_dir))
    layouts = load_layout_names()
    
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'logo', 'division', 'text', 'ip_change', 'comments']
        csvwriter = csv.DictWriter(csvfile, fieldnames=fieldnames)
        csvwriter.writeheader()

        with concurrent.futures.ProcessPoolExecutor() as executor:
            args_list = [(filename, original_dir, modified_dir, ideal_dir, layouts) for filename in original_files]
            results = executor.map(process_file, args_list)

            for result in results:
                csvwriter.writerow(result)

def main():
    original_dir = r'OnlyDXF'
    modified_dir = r'OutputDXFSMod'
    ideal_dir = r'IdealDXF'
    log_file = 'comprehensive_quality_check.csv'
    compare_multiple_files(original_dir, modified_dir, ideal_dir, log_file)

if __name__ == '__main__':
    multiprocessing.freeze_support() 
    main()
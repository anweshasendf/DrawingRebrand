import ezdxf
import os
import csv
import logging
from collections import defaultdict
import concurrent.futures
import multiprocessing

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def deep_parse_dxf(doc):
    entities = defaultdict(list)
    for entity in doc.modelspace().entity_space:
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
    
    # Compare custom data
    orig_custom = original.__dict__
    mod_custom = modified.__dict__
    all_custom_keys = set(orig_custom.keys()) | set(mod_custom.keys())
    
    for key in all_custom_keys:
        if key not in attributes:
            orig_value = orig_custom.get(key)
            mod_value = mod_custom.get(key)
            
            if orig_value != mod_value:
                if key not in orig_custom:
                    changes.append(f"Added metadata: {key} = {mod_value}")
                elif key not in mod_custom:
                    changes.append(f"Removed metadata: {key}")
                else:
                    changes.append(f"Changed metadata: {key} from {orig_value} to {mod_value}")
    
    return changes

def compare_file_size(original_file, modified_file):
    original_size = os.path.getsize(original_file)
    modified_size = os.path.getsize(modified_file)
    size_change = abs(modified_size - original_size) / original_size
    
    if size_change > 0.15:
        return f"File size changed by more than 15%: {original_size} bytes to {modified_size} bytes"
    return None

def compare_dxf_files(original_file, modified_file, ideal_file):
    original_elements = load_dxf_elements(original_file)
    modified_elements = load_dxf_elements(modified_file)
    ideal_elements = load_dxf_elements(ideal_file)
    
    results = []
    
    size_change = compare_file_size(original_file, modified_file)
    if size_change:
        results.append(('File Size', False, size_change))
    
    metadata_changes = compare_metadata(original_elements['metadata'], modified_elements['metadata'])
    for change in metadata_changes:
        results.append(('Metadata', False, change))
    
    entity_changes = compare_entities(original_elements['entities'], modified_elements['entities'], ideal_elements['entities'])
    for change in entity_changes:
        results.append(('Entity', False, change))
    
    if not any([size_change, metadata_changes, entity_changes]):
        results.append(('No Changes', True, "No changes detected"))
    
    return results

def process_file(args):
    filename, original_dir, modified_dir, ideal_dir = args
    original_file = os.path.join(original_dir, filename)
    modified_file = os.path.join(modified_dir, filename)

    if not os.path.exists(modified_file):
        return [(filename, 'File', False, f"Modified file not found: {modified_file}")]

    best_match = None
    best_match_score = float('inf')
    best_match_results = []

    for ideal_filename in os.listdir(ideal_dir):
        ideal_file = os.path.join(ideal_dir, ideal_filename)
        results = compare_dxf_files(original_file, modified_file, ideal_file)
        match_score = sum(1 for _, match, _ in results if not match)
        
        if match_score < best_match_score:
            best_match_score = match_score
            best_match = ideal_filename
            best_match_results = results

    if best_match is None:
        return [(filename, 'File', False, "No suitable ideal file found")]
    else:
        logging.info(f"Finished processing file: {filename} with best match: {best_match}")
        return [(filename, element, match, message) for element, match, message in best_match_results]

def compare_multiple_files(original_dir, modified_dir, ideal_dir, log_file):
    original_files = set(os.listdir(original_dir))
    
    with open(log_file, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Filename', 'Element', 'Match', 'Message'])

        with concurrent.futures.ProcessPoolExecutor() as executor:
            args_list = [(filename, original_dir, modified_dir, ideal_dir) for filename in original_files]
            results = executor.map(process_file, args_list)

            for file_results in results:
                for result in file_results:
                    csvwriter.writerow(result)

def main():
    original_dir = r'OnlyDXF'
    modified_dir = r'OutputDXFSMod'
    ideal_dir = r'IdealDXF'
    log_file = 'comparison_log2.csv'
    compare_multiple_files(original_dir, modified_dir, ideal_dir, log_file)

if __name__ == '__main__':
    multiprocessing.freeze_support()  
    main()
    
#Use main for parallel

#For 1 file -> 7-8 seconds 
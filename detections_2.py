import cv2
import pytesseract
import os
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\U436445\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

def preprocess_image(image):
    
    blurred = cv2.GaussianBlur(image, (5, 5), 0)
    # Normalize the image
    normalized = cv2.normalize(blurred, None, 0, 255, cv2.NORM_MINMAX)
    return normalized

def edge_detection(image):
    if len(image.shape) == 3:  # check if the image is not already grayscale
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray_image = image
    edges = cv2.Canny(gray_image, 50, 150)
    return edges

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h))
    return rotated

def template_matching(image, template, method=cv2.TM_CCOEFF_NORMED, threshold=0.55, scale_range=(0.5, 1.5), scale_steps=20, rotation_angles=[0, 90, 180, 270]):
    best_match = None
    
    h, w = template.shape[:2]
    img_h, img_w = image.shape[:2]
    
    for scale in np.linspace(scale_range[0], scale_range[1], scale_steps):
        scaled_w, scaled_h = int(w * scale), int(h * scale)
        
        if scaled_w > img_w or scaled_h > img_h:
            continue
        
        scaled_template = cv2.resize(template, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
        
        for angle in rotation_angles:
            rotated_template = rotate_image(scaled_template, angle)
            
            if rotated_template.shape[0] > img_h or rotated_template.shape[1] > img_w:
                continue
            
            try:
                result = cv2.matchTemplate(image, rotated_template, method)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                    match_val = 1 - min_val
                    match_loc = min_loc
                else:
                    match_val = max_val
                    match_loc = max_loc
                
                if best_match is None or match_val > best_match[0]:
                    best_match = (match_val, match_loc, rotated_template)
            except cv2.error:
                continue
    
    if best_match is None:
        return False, None, None
    
    return best_match[0] >= threshold, best_match[1], best_match[2]

def check_for_logo(image, logo_template):
    return template_matching(image, logo_template, threshold=0.15, scale_range=(0.8, 1.2), scale_steps=5)

def check_for_division(image, division_template):
    return template_matching(image, division_template, threshold=0.91, scale_range=(0.8, 1.2), scale_steps=10, rotation_angles=[0, 90, 180, 270])

def feature_based_matching(image, template, min_match_count=10):
    
    orb = cv2.ORB_create()
    
    
    kp1, des1 = orb.detectAndCompute(template, None)
    kp2, des2 = orb.detectAndCompute(image, None)
    
    
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    
    # Match descriptors
    matches = bf.match(des1, des2)
    
     
    matches = sorted(matches, key=lambda x: x.distance)
    
    
    good_matches = [m for m in matches if m.distance < 0.7 * matches[0].distance]
    
    if len(good_matches) > min_match_count:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        h, w = template.shape
        pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, M)
        
        return True, dst
    else:
        return False, None

def check_for_ip_note(image, ip_note_template):
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if len(ip_note_template.shape) == 3:
        ip_note_template = cv2.cvtColor(ip_note_template, cv2.COLOR_BGR2GRAY)

    h, w = image.shape[:2]
    corner_size = min(w, h) // 2  # Half of the smaller dimension

    #  search areas for all four corners
    corners = [
        image[0:corner_size, 0:corner_size],  # Top-left
        image[0:corner_size, w-corner_size:w],  # Top-right
        image[h-corner_size:h, 0:corner_size],  # Bottom-left
        image[h-corner_size:h, w-corner_size:w]  # Bottom-right
    ]

    for i, corner in enumerate(corners):
        # Template matching with lower threshold and more rotation angles
        has_match, match_loc, matched_template = template_matching(corner, ip_note_template, 
                                                                   threshold=0.6, 
                                                                   scale_range=(0.5, 1.5), 
                                                                   scale_steps=11,
                                                                   rotation_angles=[0, 90, 180, 270])
        
        if has_match:
            x, y = match_loc
            h_t, w_t = matched_template.shape[:2]
            roi = corner[y:y+h_t, x:x+w_t]
            
            # Perform edge detection on ROI and template
            roi_edges = cv2.Canny(roi, 50, 150)
            template_edges = cv2.Canny(ip_note_template, 50, 150)
            
            
            edge_similarity = cv2.matchTemplate(roi_edges, template_edges, cv2.TM_CCOEFF_NORMED)[0][0]
            
            if edge_similarity > 0.375:  # 
                
                if i == 0:  # Top-left
                    return True, (x, y), (w_t, h_t)
                elif i == 1:  # Top-right
                    return True, (w - corner_size + x, y), (w_t, h_t)
                elif i == 2:  # Bottom-left
                    return True, (x, h - corner_size + y), (w_t, h_t)
                else:  # Bottom-right
                    return True, (w - corner_size + x, h - corner_size + y), (w_t, h_t)

    return False, None, None

def check_for_text(image, text):
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    #  text detection for both horizontal and vertical orientations
    text_in_image = pytesseract.image_to_string(gray, config='--psm 3')
    text_in_image_vertical = pytesseract.image_to_string(np.rot90(gray), config='--psm 3')
    
    return text.lower() in text_in_image.lower() or text.lower() in text_in_image_vertical.lower()


def process_image(filename, image_folder, logo_template, division_template, ip_note_template, text_items):
    image_path = os.path.join(image_folder, filename)
    image = cv2.imread(image_path)
    if image is None:
        return [filename, 'Error: Unable to read image', '', '', '']

    image = preprocess_image(image)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    has_logo, logo_loc, matched_logo_template = check_for_logo(gray_image, logo_template)
    has_division, division_loc, matched_division_template = check_for_division(gray_image, division_template)
    has_ip_note, ip_note_loc, ip_note_size = check_for_ip_note(image, ip_note_template)  # Pass 'image' instead of 'gray_image'
    h, w = image.shape[:2]
    regions = [
        image[:h//3, :],  # Top third
        image[h//3:2*h//3, :],  # Middle third
        image[2*h//3:, :],  # Bottom third
        image[:, :w//3],  # Left third
        image[:, w//3:2*w//3],  # Center third
        image[:, 2*w//3:]  # Right third
    ]

    has_text = {text: any(check_for_text(region, text) for region in regions) for text in text_items}


    debug_image = image.copy()

    if has_logo:
        cv2.rectangle(debug_image, logo_loc, (logo_loc[0] + matched_logo_template.shape[1], logo_loc[1] + matched_logo_template.shape[0]), (0, 0, 255), 2)
    if has_division:
        cv2.rectangle(debug_image, division_loc, (division_loc[0] + matched_division_template.shape[1], division_loc[1] + matched_division_template.shape[0]), (0, 255, 0), 2)
    if has_ip_note and ip_note_loc is not None and ip_note_size is not None:
        cv2.rectangle(debug_image, ip_note_loc, (ip_note_loc[0] + ip_note_size[0], ip_note_loc[1] + ip_note_size[1]), (255, 0, 0), 2)

    # Save the debug image for all processed images
    debug_folder = os.path.join(image_folder, 'debug')
    os.makedirs(debug_folder, exist_ok=True)
    cv2.imwrite(os.path.join(debug_folder, f'debug_{filename}'), debug_image)

    return [
        filename,
        1 if has_logo else 0,
        1 if has_division else 0,
        1 if has_ip_note else 0,
        1 if has_text.get('danfoss', False) else 0,
        1 if has_text.get('fluid', False) else 0,
        1 if has_text.get('obsolete', False) else 0
    ]

def main(image_folder, logo_path, division_path, ip_note_path, text_items, output_csv):
    logo_template = cv2.imread(logo_path, cv2.IMREAD_GRAYSCALE)
    division_template = cv2.imread(division_path, cv2.IMREAD_GRAYSCALE)
    ip_note_template = cv2.imread(ip_note_path, cv2.IMREAD_GRAYSCALE)

    # templates are loaded correctly
    if logo_template is None:
        raise FileNotFoundError(f"Logo template not found at {logo_path}")
    if division_template is None:
        raise FileNotFoundError(f"Division template not found at {division_path}")
    if ip_note_template is None:
        raise FileNotFoundError(f"IP Note template not found at {ip_note_path}")
    
    

    log_data = []

    image_files = [f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_image, filename, image_folder, logo_template, division_template, ip_note_template, text_items) for filename in image_files]
        log_data = [future.result() for future in as_completed(futures)]

    df = pd.DataFrame(log_data, columns=['Filename', 'Logo', 'Division', 'IP Note', 'Text: Danfoss', 'Text: Fluid Division', 'Text: Obsolete Item'])
    df.to_csv(output_csv, index=False)

    summary = df.sum(numeric_only=True)
    print(summary)


if __name__ == "__main__":
    image_folder = r'C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\DrawingRebrand\Checking'
    logo_path = r'C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\DrawingRebrand\AI_Drawing_Rebranding\replcimag\Danfoss.png'
    division_path = r'C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\DrawingRebrand\AI_Drawing_Rebranding\replcimag\Danfoss_Text_2.png' or r"C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\DrawingRebrand\AI_Drawing_Rebranding\replcimag\Danfoss_Text_3.png"
    ip_note_path = r'C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\DrawingRebrand\AI_Drawing_Rebranding\replcimag\IP_note.png' 
    text_items = ['Danfoss', 'Fluid', 'obsolete']
    output_csv = 'quality_check_log.csv'
    main(image_folder, logo_path, division_path, ip_note_path, text_items, output_csv) 
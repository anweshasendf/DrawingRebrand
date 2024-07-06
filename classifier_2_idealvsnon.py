# import os
# import cv2
# import numpy as np
# from skimage.metrics import structural_similarity as ssim
# from shutil import copy2

# def create_folder(folder_name):
#     if not os.path.exists(folder_name):
#         os.makedirs(folder_name)

# def resize_image(image, width=None, height=None):
#     if width is None and height is None:
#         return image
#     h, w = image.shape[:2]
#     if width is None:
#         aspect_ratio = height / h
#         new_width = int(w * aspect_ratio)
#         new_dim = (new_width, height)
#     else:
#         aspect_ratio = width / w
#         new_height = int(h * aspect_ratio)
#         new_dim = (width, new_height)
#     return cv2.resize(image, new_dim, interpolation=cv2.INTER_AREA)

# def compare_images(imageA, imageB):
#     # Resize images to the same dimensions
#     imageA = resize_image(imageA, width=500, height=500)
#     imageB = resize_image(imageB, width=500, height=500)

#     # Convert images to grayscale
#     grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
#     grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)

#     # Compute Mean Squared Error (MSE) between two images
#     mse = np.mean((grayA - grayB) ** 2)

#     return mse
# def main(folderA, folderB, threshold=1000):
#     new_layout_folder = "New_Layout"
#     create_folder(new_layout_folder)
    
#     imagesA = [os.path.join(folderA, f) for f in os.listdir(folderA) if f.endswith(('.png', '.jpg', '.jpeg'))]
#     imagesB = [os.path.join(folderB, f) for f in os.listdir(folderB) if f.endswith(('.png', '.jpg', '.jpeg'))]
    
#     for imageA_path in imagesA:
#         imageA = cv2.imread(imageA_path)
#         is_similar = False
        
#         if imageA is None:
#             print(f"Error: Unable to read image {imageA_path}")
#             continue
        
#         for imageB_path in imagesB:
#             imageB = cv2.imread(imageB_path)
            
#             if imageB is None:
#                 print(f"Error: Unable to read image {imageB_path}")
#                 continue
            
#             resized_imageA = cv2.resize(imageA, (500, 500))
#             resized_imageB = cv2.resize(imageB, (500, 500))
            
#             mse = compare_images(resized_imageA, resized_imageB)
            
#             if mse <= threshold:
#                 is_similar = True
#                 break
        
#         if not is_similar:
#             copy2(imageA_path, new_layout_folder)
#             print(f"Moved {imageA_path} to {new_layout_folder}")
#         else:
#             destination_path = os.path.join(folderA, os.path.basename(imageA_path))
#             if not os.path.exists(destination_path):
#                 copy2(imageA_path, destination_path)
#                 print(f"Image {imageA_path} copied to source folder")
#             else:
#                 print(f"Image {imageA_path} already exists in source folder")


# if __name__ == "__main__":
#     folderA = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\ExtraImage"
#     folderB = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\ModifiedImages2"
#     main(folderA, folderB)
import cv2
import pytesseract
import os
import pandas as pd
import numpy as np

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\U436445\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Function to check for specific logos
#def check_for_logo(image, logo_template):
 #  gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
 #  result = cv2.matchTemplate(gray_image, logo_template, cv2.TM_CCOEFF_NORMED)
 #  _, max_val, _, _ = cv2.minMaxLoc(result)
 #  return max_val > 0.8
  
def check_for_logo(image, logo_template):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray_image, logo_template, cv2.TM_SQDIFF_NORMED)

    threshold = 0.1  # Adjust threshold as needed
    loc = np.where(result <= threshold)
    return len(list(zip(*loc[::-1])))

def check_for_division(image, division_template):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray_image, division_template, cv2.TM_SQDIFF_NORMED)

    threshold = 0.1  # Adjust threshold as needed
    loc = np.where(result <= threshold)
    return len(list(zip(*loc[::-1])))

def check_for_ip_note(image, ip_note_template):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray_image, ip_note_template, cv2.TM_SQDIFF_NORMED)

    threshold = 0.1  # Adjust threshold as needed
    loc = np.where(result <= threshold)
    return len(list(zip(*loc[::-1])))
    #return found
#Repeat for all 
    
# Function to check for specific text
def check_for_text(image, text):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text_in_image = pytesseract.image_to_string(gray) #was gray
    return text.lower() in text_in_image.lower()

def main(image_folder, logo_path, division_path, ip_note_path, text_items, output_csv):
    logo_template = cv2.imread(logo_path, 0)
    division_template = cv2.imread(division_path, 0)
    ip_note_template = cv2.imread(ip_note_path, 0)
    log_data = []


    for filename in os.listdir(image_folder):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(image_folder, filename)
            image = cv2.imread(image_path)
            if image is None:
                log_data.append([filename, 'Error: Unable to read image', '', '', ''])
                continue

            has_logo = check_for_logo(image, logo_template)
            has_division = check_for_division(image, division_template)
            has_ip_note = check_for_ip_note(image, ip_note_template)
            has_text = {text: check_for_text(image, text) for text in text_items}
            
            if len(image.shape) < 3:
               image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)


            log_data.append([
                filename,
                1 if has_logo else 0,
                1 if has_division else 0,
                1 if has_ip_note else 0,
                1 if has_text.get('danfoss', False) else 0,
                1 if has_text.get('fluid', False) else 0,
                1 if has_text.get('obsolete', False) else 0
            ])

    df = pd.DataFrame(log_data, columns=['Filename', 'Logo', 'Division', 'IP Note', 'Text: Danfoss', 'Text: Division', 'Text: Obsolete Item'])
    df.to_csv(output_csv, index=False)

    #summary = df.apply(pd.Series.value_counts).fillna(0).astype(int)
    summary = df.sum(numeric_only=True)
    print(summary)

if __name__ == "__main__":
    image_folder = r'C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\DrawingRebrand\Checking'
    logo_path = r'C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\DrawingRebrand\AI_Drawing_Rebranding\replcimag\Danfoss.png'
    division_path = r'C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\DrawingRebrand\AI_Drawing_Rebranding\replcimag\DanfossIndustry.png'
    ip_note_path = r'C:\Users\U436445\OneDrive - Danfoss\Documents\GitHub\DrawingRebrand\AI_Drawing_Rebranding\replcimag\IP_left.png'
    text_items = ['Danfoss', 'fluid', 'obsolete']
    output_csv = 'quality_check_log.csv'
    main(image_folder, logo_path, division_path, ip_note_path, text_items, output_csv)
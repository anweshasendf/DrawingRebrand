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
#     imageA = resize_image(imageA, width=500, height=500)  # Adjust dimensions as needed
#     imageB = resize_image(imageB, width=500, height=500)  # Adjust dimensions as needed

#     # Convert images to grayscale
#     #grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
#     #grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
    
#     grayimageA = resize_image(imageA, width=500, height=500)  # Adjust dimensions as needed was grayA
#     grayimageB = resize_image(imageB, width=500, height=500)  # Adjust dimensions as needed

    
#     # Compute SSIM between two images
#     grayimageA = np.squeeze(grayimageA)
#     grayimageB = np.squeeze(grayimageB)
#     score, _ = ssim(imageA, imageB, win_size=8, channel_axis=0)  # Adjust win_size as needed

#     return score

# def main(folderA, folderB, threshold=0.8):
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
            
#             # Resize images to the same dimensions
#             resized_imageA = cv2.resize(imageA, (500, 500))  # Resize to 500x500
#             resized_imageB = cv2.resize(imageB, (500, 500))  # Resize to 500x500
            
#             resized_imageA = np.squeeze(resized_imageA)
#             resized_imageB = np.squeeze(resized_imageB)
            
#             similarity_score = compare_images(resized_imageA, resized_imageB)
            
#             if similarity_score >= threshold:
#                 is_similar = True
#                 break
        
#         if not is_similar:
#             copy2(imageA_path, new_layout_folder)
#             print(f"Moved {imageA_path} to {new_layout_folder}")

# if __name__ == "__main__":
#     folderA = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\ExtraImage"
#     folderB = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\ModifiedImages2"
#     main(folderA, folderB)


import torch
import os
from PIL import Image
from ultralytics import YOLO
from os.path import basename, join
from os import makedirs
from typing import List

# Load pre-trained YOLOv8 model
#model = torch.hub.load('ultralytics/yolov8', 'yolov8m', pretrained=True) #Change with actual model
# Load the locally stored YOLOv8 model
model_path = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\AI_Drawing_Rebranding\version_2\runs\detect\train4\weights\best.pt"
model = YOLO(model_path) 
import os
import csv
import cv2
import numpy as np
from ultralytics import YOLO
import textwrap

def load_model(model_path):
    model = YOLO(model_path)
    return model

def load_image_paths(image_dir):
    return [os.path.join(image_dir, img) for img in os.listdir(image_dir) if img.endswith(('.jpg', '.jpeg', '.png'))]

def filter_detections(result, confidence_threshold):
    filtered_boxes = []
    if result.boxes is not None:  # Change 'result.boxes' to 'result.xyxy'
        for i, det in enumerate(result.boxes):
            if result.probs is not None and i < len(result.probs):  # Check if result.probs is not None and i is within bounds
                conf = result.probs[i]  # Confidence score
                if conf > confidence_threshold:
                    box_coords = result.orig_shape.cpu().numpy()
                    class_label = result.names[i]
                filtered_boxes.append({"class": class_label, "confidence": conf.item(), "coords": box_coords})
    return filtered_boxes

# def save_results(image, output_path, filtered_boxes, csv_output_path, image_name):
#     cv2.imwrite(output_path, image)
#     with open(csv_output_path, mode='a', newline='') as csv_file:
#         csv_writer = csv.writer(csv_file)
#         for box in filtered_boxes:
#             csv_writer.writerow([image_name, len(filtered_boxes), box["confidence"], box["class"], "Replaced"])

def save_results(image, output_path, filtered_boxes, csv_output_path, image_name):
    cv2.imwrite(output_path, image)
    with open(csv_output_path, mode='a', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        for box in filtered_boxes:
            x_center = (box["coords"][0] + box["coords"][2]) / 2
            y_center = (box["coords"][1] + box["coords"][3]) / 2
            width = box["coords"][2] - box["coords"][0]
            height = box["coords"][3] - box["coords"][1]
            csv_writer.writerow([image_name, box["class"], x_center, y_center, width, height])
            
            # Create annotation .txt file
            txt_filename = os.path.splitext(image_name)[0] + ".txt"
            txt_path = os.path.join(os.path.dirname(image_name), txt_filename)
            with open(txt_path, 'a') as txt_file:
                txt_file.write(f"{box['class']} {x_center} {y_center} {width} {height}\n")
def main():
    current_directory = os.getcwd()
    model_path = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\AI_Drawing_Rebranding\version_2\runs\detect\train4\weights\best.pt"

    image_dir = os.path.join(current_directory, "ExtraImage")
    csv_output_path = os.path.join(current_directory, "detection_logs.csv")
    output_folder = os.path.join(current_directory, "OutputImages")
    os.makedirs(output_folder, exist_ok=True)
    
    model = load_model(model_path)
    image_paths = load_image_paths(image_dir)
    csv_headers = ["Image", "Detections", "Confidence", "Class", "Status"]
    with open(csv_output_path, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(csv_headers)

    for image_path in image_paths:
        image_name = os.path.basename(image_path)
        output_path = os.path.join(output_folder, image_name)

        original_image = cv2.imread(image_path)
        if original_image is None:
            print(f"Failed to load image {image_path}. Skipping.")
            continue

        results = model(image_path)
        filtered_boxes = filter_detections(results[0], confidence_threshold=0.3)
        if not filtered_boxes:
            print(f"No detections above confidence threshold in image {image_path}")
            continue

        modified_image = filter_detections(original_image.copy(), filtered_boxes)
        save_results(modified_image, output_path, filtered_boxes, csv_output_path, image_name)
        print(f"Processed and saved modified image: {output_path}")

if __name__ == "__main__":
    main()
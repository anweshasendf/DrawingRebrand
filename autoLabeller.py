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


def predict_and_save(image_path, output_dir):
    # Load image
    image = Image.open(image_path)
    
    # Perform inference
    results = model(image)
    
    # Extract predictions
     # Extract predictions
    yolo_annotations: List[str] = []
    for result in results:
        # Get bounding box coordinates and class probabilities
        boxes = result.boxes
        #probs = result.probs
        confs = boxes.data[:, 0:6]
        #bbox = result.boxes.xyxy[:].cpu().numpy()
        
        # Iterate over each bounding box
        for bbox, confs in zip(boxes, confs):
            # Convert bounding box coordinates to YOLO format
            if len(bbox) <= 4:
                continue
        
            # Convert bounding box coordinates to YOLO format
            x_center = (bbox[0] + bbox[2]) / 2 if len(bbox) >= 3 else 0
            y_center = (bbox[1] + bbox[3]) / 2 if len(bbox) >= 4 else 0
            width = (bbox[2] - bbox[0]) if len(bbox) >= 3 else 0
            height = (bbox[3] - bbox[1]) if len(bbox) >= 4 else 0
           
            
            # Get class with highest probability
            class_id = confs.argmax()
            
            # Append annotation to list
            # Append annotation to list
            annotation = f"{class_id} {x_center} {y_center} {width} {height}"
            yolo_annotations.append(annotation)
    
    # Save annotations to file
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}.txt")
    with open(output_path, 'w') as f:
        f.write("\n".join(yolo_annotations))

# Example usage
image_dir = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\ExtraImage"
output_dir = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\NewAnnotations"
os.makedirs(output_dir, exist_ok=True)

for image_file in os.listdir(image_dir):
    if image_file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        image_path = os.path.join(image_dir, image_file)
        predict_and_save(image_path, output_dir)

print("Auto-labeling complete!")
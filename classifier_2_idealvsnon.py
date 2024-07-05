import os
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from shutil import copy2

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

def resize_image(image, width=None, height=None):
    if width is None and height is None:
        return image
    h, w = image.shape[:2]
    if width is None:
        aspect_ratio = height / h
        new_width = int(w * aspect_ratio)
        new_dim = (new_width, height)
    else:
        aspect_ratio = width / w
        new_height = int(h * aspect_ratio)
        new_dim = (width, new_height)
    return cv2.resize(image, new_dim, interpolation=cv2.INTER_AREA)

def compare_images(imageA, imageB):
    # Resize images to the same dimensions
    imageA = resize_image(imageA, width=500, height=500)
    imageB = resize_image(imageB, width=500, height=500)

    # Convert images to grayscale
    grayA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
    grayB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)

    # Compute Mean Squared Error (MSE) between two images
    mse = np.mean((grayA - grayB) ** 2)

    return mse
def main(folderA, folderB, threshold=1000):
    new_layout_folder = "New_Layout"
    create_folder(new_layout_folder)
    
    imagesA = [os.path.join(folderA, f) for f in os.listdir(folderA) if f.endswith(('.png', '.jpg', '.jpeg'))]
    imagesB = [os.path.join(folderB, f) for f in os.listdir(folderB) if f.endswith(('.png', '.jpg', '.jpeg'))]
    
    for imageA_path in imagesA:
        imageA = cv2.imread(imageA_path)
        is_similar = False
        
        if imageA is None:
            print(f"Error: Unable to read image {imageA_path}")
            continue
        
        for imageB_path in imagesB:
            imageB = cv2.imread(imageB_path)
            
            if imageB is None:
                print(f"Error: Unable to read image {imageB_path}")
                continue
            
            resized_imageA = cv2.resize(imageA, (500, 500))
            resized_imageB = cv2.resize(imageB, (500, 500))
            
            mse = compare_images(resized_imageA, resized_imageB)
            
            if mse <= threshold:
                is_similar = True
                break
        
        if not is_similar:
            copy2(imageA_path, new_layout_folder)
            print(f"Moved {imageA_path} to {new_layout_folder}")
        else:
            destination_path = os.path.join(folderA, os.path.basename(imageA_path))
            if not os.path.exists(destination_path):
                copy2(imageA_path, destination_path)
                print(f"Image {imageA_path} copied to source folder")
            else:
                print(f"Image {imageA_path} already exists in source folder")


if __name__ == "__main__":
    folderA = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\ExtraImage"
    folderB = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\ModifiedImages2"
    main(folderA, folderB)

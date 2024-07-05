import os
import shutil
import cv2
import numpy as np
from sklearn.cluster import KMeans
from sklearn.cluster import AgglomerativeClustering
from shutil import move, copy

# Function to extract features from an image
def extract_features(image_path):
    # Add your feature extraction logic here
    image = cv2.imread(image_path)
    # Example: Extract size and layout features
    #size_feature = np.mean(image.shape[:2])  # Example feature based on size
    layout_feature = np.sum(image)  # Example feature based on layout
    #return np.array([size_feature, layout_feature])
    return np.array([layout_feature])

def get_image_files(input_folder):
    image_files = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(root, file))
    return image_files

# Path to the input folder containing images
input_folder = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\ExtraImage"

# Path to the output folder where the subfolders will be created
output_folder = r"C:\Users\U436445\OneDrive - Danfoss\Documents\Codes\DrawingRebrand\TestImages"

image_files = get_image_files(input_folder)

# Extract features for all images
features = [extract_features(os.path.join(input_folder, f)) for f in image_files]

# Cluster the images using K-means clustering
k = min(25, len(image_files))  # Limit to 25 clusters
kmeans = KMeans(n_clusters=k, random_state=0).fit(features)

clustering = AgglomerativeClustering(n_clusters=k).fit(features)

labels = clustering.labels_

# Create folders for each cluster and move images
for i in range(k):
    cluster_folder = os.path.join(output_folder, f"Cluster_{i}")
    os.makedirs(cluster_folder, exist_ok=True)
    cluster_indices = [j for j, label in enumerate(labels) if label == i]
    if len(cluster_indices) == 1:
        unique_folder = os.path.join(output_folder, "Unique")
        if not os.path.exists(unique_folder):
            os.makedirs(unique_folder)
        shutil.copy(os.path.join(input_folder, image_files[cluster_indices[0]]), unique_folder)
    else:
        for j in cluster_indices:
            shutil.copy(os.path.join(input_folder, image_files[j]), cluster_folder)

# Create "Unique" folder for images that do not fit into any cluster
unique_folder = os.path.join(output_folder, "Unique")
os.makedirs(unique_folder, exist_ok=True)
for j, image_file in enumerate(image_files):
    if labels[j] == -1:
        shutil.copy(os.path.join(input_folder, image_file), unique_folder)
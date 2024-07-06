import subprocess
import sys
import os

def launch_labelimg():
    # Check if LabelImg is installed
    try:
        # Try to import labelImg to check if it's installed
        import labelImg
        labelimg_path = os.path.dirname(labelImg.__file__)
        
        # Construct the path to the main script
        main_script = os.path.join(labelimg_path, 'labelImg.py')
        
        # Launch LabelImg
        subprocess.run([sys.executable, main_script])
    except ImportError:
        print("LabelImg is not installed. Please install it using:")
        print("pip install labelImg")
        sys.exit(1)

if __name__ == "__main__":
    launch_labelimg()
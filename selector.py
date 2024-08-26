import time
import pyautogui

def manual_select_and_download(files_per_batch=1200):
    while True:
        print(f"Please manually select {files_per_batch} files.")
        print("Use the following process:")
        print("1. Click on the first file to select it.")
        print("2. Scroll down to the last file you want to select.")
        print("3. Hold Shift and click on the last file to select all files in between.")
        print("4. If needed, repeat steps 2-3 until you've selected approximately 1200 files.")
        
        input("Press Enter when you've selected approximately 1200 files...")
        
        print("Now, please click the download button.")
        input("Press Enter after clicking the download button...")
        
        print("Waiting for 2 minutes for the download to complete...")
        for i in range(120, 0, -1):
            print(f"Time remaining: {i} seconds", end='\r')
            time.sleep(1)
        print("\nDownload time complete.")
        
        print("Please deselect all files:")
        print("1. Click the 'Select all' checkbox to deselect all files.")
        input("Press Enter after deselecting all files...")
        
        continue_selection = input("Do you want to select and download another batch? (y/n): ").lower()
        if continue_selection != 'y':
            break

    print("Process complete. Thank you!")

# Run the manual selection and download process
manual_select_and_download()
import os

def find_acad_exe():
    for root, dirs, files in os.walk("C:\\"):  # Start searching from the C: drive
        for file in files:
            if file.lower() == "acad.exe":
                return os.path.join(root, file)
    return None

def find_shx_directories():
    shx_directories = set()
    for root, dirs, files in os.walk("C:\\"):  # Start searching from the C: drive
        for file in files:
            if file.lower().endswith(".shx"):
                shx_directories.add(root)
    return shx_directories

def main():
    acad_path = find_acad_exe()
    if acad_path:
        print(f"AutoCAD executable found at: {acad_path}")
    else:
        print("AutoCAD executable (acad.exe) not found.")
        print("Searching for directories containing .shx files...")
        shx_dirs = find_shx_directories()
        if shx_dirs:
            print("Directories containing .shx files:")
            for dir in shx_dirs:
                print(dir)
        else:
            print("No directories containing .shx files found.")

if __name__ == "__main__":
    main()
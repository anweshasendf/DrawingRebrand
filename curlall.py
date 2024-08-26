import os
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.client_credential import ClientCredential

# Replace these variables with your details
site_url = "https://danfoss-my.sharepoint.com/personal/priyanshu_chatuphale_danfoss_com"
client_id = "c4053e38-ad1d-4453-9883-da953a7757b2"
client_secret = "zPJ8Q~VWF.IseInAIl8NJ3umadCWRSikKRffLbzi"
folder_url = "/personal/priyanshu_chatuphale_danfoss_com/Documents/Metal Rebranding_AutoCAD/15000_DS_1"  # SharePoint folder relative URL
local_dir = "all15k"  # Local directory where you want to save the files

# Set up authentication
credentials = ClientCredential(client_id, client_secret)
ctx = ClientContext(site_url).with_credentials(credentials)

def download_files_from_folder(sp_folder, local_folder):
    """Recursively download files from SharePoint folder to local directory"""
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    # Get files in the current folder
    files = sp_folder.files
    ctx.load(files)
    ctx.execute_query()

    for sp_file in files:
        local_file_path = os.path.join(local_folder, sp_file.name)
        with open(local_file_path, 'wb') as local_file:
            sp_file.download(local_file).execute_query()
        print(f"Downloaded: {sp_file.name}")

    # Recursively download subfolders
    folders = sp_folder.folders
    ctx.load(folders)
    ctx.execute_query()

    for folder in folders:
        folder_name = folder.properties["Name"]
        download_files_from_folder(folder, os.path.join(local_folder, folder_name))

# Get the target SharePoint folder
target_folder = ctx.web.get_folder_by_server_relative_url(folder_url)
ctx.load(target_folder)
ctx.execute_query()

# Start downloading
download_files_from_folder(target_folder, local_dir)

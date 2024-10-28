import bpy
import sys
import os
from pathlib import Path
import time
import threading
import requests
from bpy.app.handlers import persistent


####################################################################################################
# Import header
from .header import (
    REMI_HD_Info_Message
)

####################################################################################################
def get_roaming_folder():
    # Set the default encoding to UTF-8
    if sys.platform.startswith('win'):
        # On Windows
        os.environ['PYTHONUTF8'] = '1'
    else:
        # On other platforms (e.g., Linux, macOS)
        sys.setdefaultencoding('utf-8')

    # Get the home directory using Path.home()
    home = Path.home()
    if sys.platform == "win32":
        return os.path.join(home,'AppData','Roaming')
    elif sys.platform == "linux":
        return os.path.join(home,'.local','share')
    elif sys.platform == "darwin":
        return os.path.join(home,'Library','Application Support')

def update_info_message(self, context):
    pass

def update_percentage_download(self, context):
    wm = context.window_manager
    if(wm.remi_re_update_percentage == 100):
        wm.remi_re_update_percentage = 0
        report_info('Finished Update Assets Browser.')

def report_info(message):
    # Set message
    bpy.context.window_manager.remi_re_info_message = message
    def draw_info():
        bpy.types.STATUSBAR_HT_header.remove(REMI_HD_Info_Message.draw)
        bpy.types.STATUSBAR_HT_header.append(REMI_HD_Info_Message.draw)
        time.sleep(2)
        bpy.types.STATUSBAR_HT_header.remove(REMI_HD_Info_Message.draw)
    t = threading.Thread(target=draw_info,args=())
    t.start()

# Path variable
pathname = 'Remi Library'
roaming_folder = get_roaming_folder()
assets_browser_path = os.path.join(roaming_folder, pathname, 'assets')
downloaded_folder = os.path.join(assets_browser_path, "downloaded")
proxies_folder = os.path.join(assets_browser_path, "proxies")
geometry_nodes_folder = os.path.join(assets_browser_path, "geometry_nodes")

def assign_remi_library_path():
    Path(downloaded_folder).mkdir(parents=True, exist_ok=True)
    Path(proxies_folder).mkdir(parents=True, exist_ok=True)
    Path(geometry_nodes_folder).mkdir(parents=True, exist_ok=True)

    # Check if Remi Library already in path, if not, create it
    asset_libraries = bpy.context.preferences.filepaths.asset_libraries
    if not pathname in asset_libraries:
        bpy.ops.preferences.asset_library_add()
        new_library = bpy.context.preferences.filepaths.asset_libraries[-1]

        new_library.name = pathname
        new_library.path = assets_browser_path

    # Download assets cats from url
    url = "https://remitriadi.com/api/getAssetCats"
    response = requests.get(url)

    # Write assets cats to roaming folder, it will update everytime the cats assets change in the server
    if response.status_code == 200:
        outputs_lines = response.text.split("\\r\\n")
        output_string = "\n".join(outputs_lines).replace('"',"")
        with open(os.path.join(assets_browser_path, 'blender_assets.cats.txt'), "w") as f:
            f.write(output_string)

def update_assets_browser():
    # Purge all corrupted proxies
    proxies_list = os.listdir(proxies_folder)
    for proxies_file in proxies_list:
        proxies_filepath = os.path.join(proxies_folder, proxies_file)
        file_stats = os.stat(proxies_filepath)
        #Purge corrupted
        if(file_stats.st_size < 10000):
            os.remove(proxies_filepath)
        # Purge duplicated in downloaded
        downloaded_filepath = os.path.join(downloaded_folder, proxies_file)
        if(os.path.exists(downloaded_filepath)):
            os.remove(proxies_filepath)

    # Request to backend
    # Download all geonodes to geonodes folder
    def update_geonodes():
        url = "https://remitriadi.com/api/getAllGeoNodesName"
        r = requests.get(url)

        geonodes_online = sorted(r.json())
        # Start Updating
        for geonode in geonodes_online:
            # Check if it's not in downloaded folder and proxies folder
            url = f"http://remitriadi.org/geometry_nodes/{geonode}.blend"
            response = requests.get(url)
            open(os.path.join(geometry_nodes_folder, f"{geonode}.blend"), "wb").write(response.content)

    # Download assets to proxies folder
    def update_asset():
        wm = bpy.context.window_manager
        url = "https://remitriadi.com/api/getAllAssetsName"
        r = requests.get(url)
        
        # Online Assets
        online_assets = sorted(r.json())

        # Offline Assets
        def get_assets_list_from_folder():
            downloaded_list = os.listdir(downloaded_folder)
            proxies_list = os.listdir(proxies_folder)
            all_list = downloaded_list + proxies_list
            filtered_list = list(filter(lambda x: '.blend' in x, all_list))
            map_list = [item.replace(".blend","") for item in filtered_list]
            return map_list
        
        offline_assets = get_assets_list_from_folder()
        
        # Asset to be downloaded
        assets_to_be_downloaded = []
        for asset in online_assets:
            if asset not in offline_assets:
                assets_to_be_downloaded.append(asset)

        total_assets = len(assets_to_be_downloaded)
        # Start Updating
        for index, asset in enumerate(assets_to_be_downloaded):
            # Check if it's not in downloaded folder and proxies folder
            url = f"http://remitriadi.org/proxies/{asset}.blend"
            response = requests.get(url)
            open(os.path.join(proxies_folder, f"{asset}.blend"), "wb").write(response.content)

            #If finished
            if index == total_assets - 1:
                wm.remi_re_update_percentage = 100
                # Delete handler after finished
                # Unregister handlers
                for h in bpy.app.handlers.save_post:
                    if h.__name__ == 'assign_remi_library_handler':
                        bpy.app.handlers.load_post.remove(h)
            else:
                #Update download
                percentage = (index/total_assets) * 100
                wm.remi_re_update_percentage = percentage
                report_info(f"Updating new Remi Library assets: {index + 1}/{total_assets}.")
    
    def update_all():
        update_geonodes()
        update_asset()

    t = threading.Thread(target=update_all, args=())
    t.start()

####################################################################################################
@persistent
def assign_remi_library_handler(dummy):
    assign_remi_library_path()
    update_assets_browser()

####################################################################################################
from .remi_asset_browser import (register as remi_ab_register, unregister as remi_ab_unregister)

installers = [
    remi_ab_register
]

uninstallers = [
    remi_ab_unregister
]

def install_all_addons():
    for installer in installers:
        try:
            installer()
        except:
            pass

def uninstall_all_addons():
    for uninstaller in uninstallers:
        try:
            uninstaller()
        except:
            pass
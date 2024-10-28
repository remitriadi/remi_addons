bl_info = {
    "name": "Remi Addons V.1.0.0",
    "author": "Remi Triadi<remitriadi@gmail..com>",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "category": "Remi Addons",
    "location": "On 3D viewport properties tab.",
    "description": "Assets Browser curated by Remi Triadi",
    "doc_url": "https://remitriadi.com",
    "tracker_url": "",
}

# Import other modules
import bpy
import ssl

# Set ssl so macos can create https requests
ssl._create_default_https_context = ssl._create_unverified_context

# Import Operator
from .operator import (
    REMI_OT_Report_Info
)

from .util import(
    update_percentage_download,
    update_info_message,
    assign_remi_library_handler,
    install_all_addons,
    uninstall_all_addons
)

classes = [
    REMI_OT_Report_Info
]    

        
def register():     
    from bpy.types import WindowManager, Scene, PropertyGroup
    from bpy.props import BoolProperty, StringProperty, IntProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty

    # Register classes
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except:
            pass

    # Window Manager
    WindowManager.remi_re_update_percentage = FloatProperty(
        name="Updating...", 
        subtype="PERCENTAGE",
        soft_min=0, 
        soft_max=100, 
        precision=2,
        update = update_percentage_download
    )

    WindowManager.remi_re_info_message = StringProperty(
        subtype = 'DIR_PATH',
        default= '',
        update=update_info_message
    )

    # Install all addons
    install_all_addons()
    
    #Register handlers
    bpy.app.handlers.load_post.append(assign_remi_library_handler)

def unregister():
    from bpy.types import WindowManager, Scene, PropertyGroup

    # Unregister handlers
    for h in bpy.app.handlers.save_post:
        if h.__name__ == 'assign_remi_library_handler':
            bpy.app.handlers.load_post.remove(h)

    uninstall_all_addons()
    # Delete all Window Manager
    del WindowManager.remi_re_update_percentage
    del WindowManager.remi_re_info_message


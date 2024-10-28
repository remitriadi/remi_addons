# Import Main Module
import bpy
import os
import time

# Import firebase
path_to_remi_addons = os.path.dirname(os.path.abspath(__file__))

# Import util
from .util import (remi_asset_browser_append, remi_asset_browser_link,update_download_progress, update_link_object_pointer, update_percentage)

classes = []

def register():      
    from bpy.types import WindowManager, Scene, PropertyGroup
    from bpy.props import BoolProperty, StringProperty, IntProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty

    #Clear collection update handler
    for h in bpy.app.handlers.depsgraph_update_post:
        if h.__name__ == 'remi_asset_browser_append':
            bpy.app.handlers.depsgraph_update_post.remove(h)
        if h.__name__ == 'remi_asset_browser_link':
            bpy.app.handlers.depsgraph_update_post.remove(h)

    bpy.app.handlers.depsgraph_update_post.append(remi_asset_browser_append)
    bpy.app.handlers.depsgraph_update_post.append(remi_asset_browser_link)

    for cls in classes:
        bpy.utils.register_class(cls)

    WindowManager.remi_ab_object_pointer = PointerProperty(
        type=bpy.types.Object,
    )

    WindowManager.remi_ab_link_object_pointer = PointerProperty(
        type=bpy.types.Object,
        update=update_link_object_pointer
    )

    WindowManager.remi_ab_download_progress = FloatProperty(
        default=0,
        update = update_download_progress
    )

    WindowManager.remi_ab_download_state = BoolProperty(
        default=False
    )
    WindowManager.remi_ab_path_to_write = StringProperty(
        default=''
    )
    
    WindowManager.remi_ab_update_state = BoolProperty(
        default=False
    )

    WindowManager.remi_ab_update_percentage = FloatProperty(
        name="Updating...", 
        subtype="PERCENTAGE",
        soft_min=0, 
        soft_max=100, 
        precision=2,
        update = update_percentage
    )

    WindowManager.remi_ab_zip_percentage = FloatProperty(
        name="Zipping...", 
        subtype="PERCENTAGE",
        soft_min=0, 
        soft_max=100, 
        precision=0,
        update = update_percentage
    )
    
def unregister():
    from bpy.types import WindowManager, Scene, PropertyGroup
    #Clear collection update handler
    for h in bpy.app.handlers.depsgraph_update_post:
        if h.__name__ == 'remi_asset_browser_append':
            bpy.app.handlers.depsgraph_update_post.remove(h)
        if h.__name__ == 'remi_asset_browser_link':
            bpy.app.handlers.depsgraph_update_post.remove(h)

    # Unintsall Class
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del WindowManager.remi_ab_path_to_write
    del WindowManager.remi_ab_object_pointer
    del WindowManager.remi_ab_link_object_pointer
    del WindowManager.remi_ab_download_progress
    del WindowManager.remi_ab_download_state
    del WindowManager.remi_ab_update_state
    del WindowManager.remi_ab_update_percentage

    
import bpy
from bpy.app.handlers import persistent
from mathutils import Vector, Matrix
import gpu
from gpu_extras.batch import batch_for_shader
import math
from functools import reduce

import threading
import requests
import os
import blf
from bpy_extras import view3d_utils
from pathlib import Path
from ..util import (report_info,  get_roaming_folder)

roaming_folder = get_roaming_folder()
assets_browser_path = os.path.join(roaming_folder, 'Remi Library','assets')

###################################################################
def sum_vector(a,b):
    return a+b

###################################################################
def draw_grid_overlay(grid_count, ob):
    #Grid Object
    matrix = ob.matrix_local.inverted()
    grid_length = ob.dimensions.x if ob.dimensions.x > ob.dimensions.y else ob.dimensions.y

    # Get pivot
    vertices = ob.data.vertices

    world_position = [ob.matrix_world @ vertex.co for vertex in vertices]
    world_average_position = reduce(sum_vector, world_position)
    center_world_position = world_average_position/len(vertices)

    z = (ob.dimensions.z * 1.00/2)

    for i in range(-grid_count,grid_count+1):
        i_n = i/grid_count
        index = math.radians(i_n * 90)
        
        precision = 1000
        l = round(math.cos(index) * precision) / precision
        l = math.sqrt(l)
        l = l * grid_length
        d = i_n * grid_length
        

        grid_ov = {
            'x_p':Vector([l,d,-z]),
            'x_n':Vector([-l,d,-z]),
            'x_o':Vector([0,d,-z]),

            'y_p':Vector([d,l,-z]),
            'y_n':Vector([d,-l,-z]),
            'y_o':Vector([d,0,-z]),
        }

        for vertex in grid_ov:
            grid_ov[vertex] = grid_ov[vertex] @ matrix
            grid_ov[vertex] = Vector([
                grid_ov[vertex].x + center_world_position.x,
                grid_ov[vertex].y + center_world_position.y, 
                grid_ov[vertex].z + center_world_position.z
            ])

        color_start = (1,1,1,0.3)
        color_end = (1,1,1,0)

        # X
        draw_line_3d_smooth(grid_ov['x_o'],grid_ov['x_p'],color_start,color_end)
        draw_line_3d_smooth(grid_ov['x_o'],grid_ov['x_n'],color_start,color_end)

        # Y
        draw_line_3d_smooth(grid_ov['y_o'],grid_ov['y_p'],color_start,color_end)
        draw_line_3d_smooth(grid_ov['y_o'],grid_ov['y_n'],color_start,color_end)

        #Axis
        color_start = (1,1,1,1)
        color_end = (1,1,1,0)

        multiplier = 1
        o = Vector([0,0,-z])
        x_p = Vector([grid_length*multiplier,0,-z])
        x_n = Vector([-grid_length*multiplier,0,-z])
        y_p = Vector([0,grid_length*multiplier,-z])
        y_n = Vector([0,-grid_length*multiplier,-z])

        vertices = [o, x_p, x_n, y_p, y_n]
        for vertex,_ in enumerate(vertices):
            vertices[vertex] = vertices[vertex] @ matrix
            vertices[vertex] = Vector([
                vertices[vertex].x + center_world_position.x,
                vertices[vertex].y + center_world_position.y, 
                vertices[vertex].z + center_world_position.z
            ])

        draw_line_3d_smooth(vertices[0],vertices[1],color_start,color_end)
        draw_line_3d_smooth(vertices[0],vertices[2],color_start,color_end)
        draw_line_3d_smooth(vertices[0],vertices[3],color_start,color_end)
        draw_line_3d_smooth(vertices[0],vertices[4],color_start,color_end)

###################################################################

def draw_bounding_box(ob, color):
    #Grid Object
    matrix = ob.matrix_local.inverted()

    # Get pivot
    vertices = ob.data.vertices

    world_position = [ob.matrix_world @ vertex.co for vertex in vertices]
    world_average_position = reduce(sum_vector, world_position)
    center_world_position = world_average_position/len(vertices)

    x = (ob.dimensions.x * 1.00/2)
    y = (ob.dimensions.y * 1.00/2)
    l = (ob.dimensions.z/15)
    z = (ob.dimensions.z * 1.00/2)

    # X,-Y,Z
    p3 = Vector([-x,y,z]) 
    p13 = Vector([-x,y-l,z]) 
    p22 = Vector([-x+l,y,z]) 
    p17 = Vector([-x,y,z-l]) 

    # -X,-Y,Z
    p7 = Vector([x,y,z]) 
    p15 = Vector([x,y-l,z]) 
    p9 = Vector([x-l,y,z]) 
    p18 = Vector([x,y,z-l]) 

    # -X,Y,Z
    p5 = Vector([x,-y,z]) 
    p11 = Vector([x-l,-y,z]) 
    p19 = Vector([x,-y,z-l]) 
    p25 = Vector([x,-y+l,z]) 

    # X,Y,Z
    p1 = Vector([-x,-y,z]) 
    p21 = Vector([-x+l,-y,z]) 
    p26 = Vector([-x,-y+l,z]) 
    p16 = Vector([-x,-y,z-l]) 

    # X,Y,-Z
    p6 = Vector([x,y,-z])
    p14 = Vector([x,y-l,-z])
    p8 = Vector([x-l,y,-z])
    p29 = Vector([x,y,-z+l])

    # X,-Y,-Z
    p4 = Vector([x,-y,-z])
    p10 = Vector([x-l,-y,-z])
    p30 = Vector([x,-y,-z+l])
    p27 = Vector([x,-y+l,-z])

    # -X,-Y,-Z
    p0 = Vector([-x,-y,-z])
    p24 = Vector([-x,-y+l,-z])
    p31 = Vector([-x,-y,-z+l])
    p23 = Vector([-x+l,-y,-z])

    # -X,Y,-Z
    p2 = Vector([-x,y,-z])
    p20 = Vector([-x+l,y,-z])
    p28 = Vector([-x,y,-z+l])
    p12 = Vector([-x,y-l,-z])
    
    # Create all angle
    a1 = [p3, p13, p22, p17]
    a2 = [p7, p15, p9, p18]
    a3 = [p5, p11, p19, p25]
    a4 = [p1, p21, p26, p16]

    a5 = [p6, p14, p8, p29]
    a6 = [p4, p10, p30, p27]
    a7 = [p0, p24, p31, p23]
    a8 = [p2, p20, p28, p12]

    vertices = [a1, a2, a3, a4, a5, a6, a7, a8]
    
    for angle in vertices:
        for index,_ in enumerate(angle):
            angle[index] = angle[index] @ matrix
            angle[index] = Vector([
                angle[index].x + center_world_position.x,
                angle[index].y + center_world_position.y, 
                angle[index].z + center_world_position.z
            ])

        # Draw Box Gui
        draw_line_3d(color, angle[0], angle[1])
        draw_line_3d(color, angle[0], angle[2])
        draw_line_3d(color, angle[0], angle[3])
    
###################################################################
def draw_line_3d(color, start, end):
    # shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
    gpu.state.line_width_set(0.5)
    shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
    color_blend = (color, color)
    batch = batch_for_shader(shader, 'LINES', {"pos": [start,end], "color":color_blend})
    shader.bind()
    batch.draw(shader)

###################################################################
def draw_line_3d_smooth(posStart, posEnd, colorStart, colorEnd):
    gpu.state.line_width_set(0.5)
    coord1 = Vector(posStart)
    coord2 = Vector(posEnd)
    coords = [coord1, coord2]
    colors = [colorStart,colorEnd]

    shader = gpu.shader.from_builtin('POLYLINE_SMOOTH_COLOR')
    batch = batch_for_shader(shader, 'LINES', {"pos": coords, "color": colors})
    shader.bind()
    batch.draw(shader)

###################################################################
def draw_callback_2d():
    # Init GPU State
    gpu.state.blend_set("ALPHA")
    gpu.state.depth_test_set("LESS")
    try:
        selected_asset = bpy.context.window_manager.remi_ab_object_pointer
        progress = bpy.context.window_manager.remi_ab_download_progress
        asset_name = selected_asset.name
        current_progress = round(float(progress) * 100)
        if(current_progress == 0):
            full_name =  f"{asset_name}"
        else:
            full_name =  f"{asset_name} {current_progress}%"
        draw_typo_2d((1.0, 1.0, 1.0, 1.0), full_name, selected_asset.location)
    except:
        pass

    # Restore GPU State
    gpu.state.blend_set("NONE")
    gpu.state.depth_test_set("NONE")

###################################################################
path_to_py = Path(os.path.abspath(__file__))
ttf_path = os.path.join(path_to_py.parent, "RobotoMono-Regular.ttf")
font_id = blf.load(ttf_path)

def draw_typo_2d(color, text, location):
    region = bpy.context.region
    rv3d = bpy.context.region_data
    mouse_loc = view3d_utils.location_3d_to_region_2d(region, rv3d, location)

    offset = 30
    blf.color(font_id, color[0], color[1], color[2], color[3])
    blf.position(font_id, mouse_loc.x + offset, mouse_loc.y, 0)
    blf.size(font_id, 20)
    blf.draw(font_id, text)
###################################################################

def draw_tris_3d(coords):
    vertex_shader = '''
        uniform mat4 viewProjectionMatrix;

        in vec3 position;
        out vec3 pos;

        void main()
        {
            pos = position;
            gl_Position = viewProjectionMatrix * vec4(position, 1.0f);
        }
    '''

    fragment_shader = '''
        in vec3 pos;
        out vec4 FragColor;

        void main()
        {
            FragColor = vec4(vec3(0.0,1.0,0.37), 0.05);
        }
    '''

    shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
    batch = batch_for_shader(shader, 'TRIS', {"position": coords})

    shader.bind()
    matrix = bpy.context.region_data.perspective_matrix
    shader.uniform_float("viewProjectionMatrix", matrix)
    batch.draw(shader)

###################################################################

def draw_loading_bar(height, ob):
    location = ob.location
    matrix = ob.matrix_world.inverted()
    dimensions = ob.dimensions

    x = dimensions.x / 2
    y = dimensions.y / 2
    z = dimensions.z / 2

    # Get pivot
    vertices = ob.data.vertices

    world_position = [ob.matrix_world @ vertex.co for vertex in vertices]
    world_average_position = reduce(sum_vector, world_position)
    center_world_position = world_average_position/len(vertices)

    p0 = Vector([-x,-y,-z])
    p1 = Vector([x,-y,-z])
    p2 = Vector([-x,y,-z])
    p3 = Vector([x,y,-z])
    p4 = Vector([-x,-y, height-z])
    p5 = Vector([x,-y,height-z])
    p6 = Vector([-x,y,height-z])
    p7 = Vector([x,y,height-z])

    # Left
    tris0 = [p0,p6,p4]
    tris1 = [p0,p2,p6]
    # Right
    tris2 = [p5,p1,p7]
    tris3 = [p1,p3,p7]
    # Up
    tris4 = [p6,p4,p5]
    tris5 = [p5,p7,p6]
    # Bottom
    tris6 = [p0,p1,p2]
    tris7 = [p2,p1,p3]
    # Front 
    tris8 = [p2,p7,p6]
    tris9 = [p2,p3,p7]
    # Back
    tris10 = [p4,p0,p5]
    tris11 = [p0,p1,p5]

    triangles = [
        tris0, 
        tris1, 
        tris2, 
        tris3, 
        tris4, 
        tris5, 
        tris6, 
        tris7, 
        tris8, 
        tris9, 
        tris10, 
        tris11
    ]
    for tris_index,tris_coord in enumerate(triangles):
        for index,p in enumerate(tris_coord):
            tris_coord[index] = p @ matrix
            tris_coord[index] = Vector([
                tris_coord[index].x + center_world_position.x,
                tris_coord[index].y + center_world_position.y, 
                tris_coord[index].z + center_world_position.z
            ])

        #If progress still 0, don't draw tris_coord
        if height != 0:
            draw_tris_3d(tris_coord)

###################################################################

def draw_callback_3d():
    # Init GPU State
    gpu.state.blend_set("ALPHA")
    gpu.state.depth_test_set("LESS")

    # Enabled renderer
    try:
        ob = bpy.context.window_manager.remi_ab_object_pointer
        # # Grid Overlay
        grid_count = 10
        draw_grid_overlay(grid_count,  ob)
        
        # Bounding Box
        color = (0.96,0.94,0.3,1)
        draw_bounding_box(ob, color)
        
        # Loading Bar
        height = ob.dimensions.z * bpy.context.window_manager.remi_ab_download_progress
        draw_loading_bar(height, ob)
    except:
        pass
    
    # Restore GPU State
    gpu.state.blend_set("NONE")
    gpu.state.depth_test_set("NONE")


###################################################################
def download_asset(handler3d, handler2d, download_url):
    #Set download state
    wm = bpy.context.window_manager
    wm.remi_ab_download_state = True
    
    # Write Blender file to addons folder
    with open(wm.remi_ab_path_to_write, "wb") as f:
        response = requests.get(download_url, stream=True)
        total_length = response.headers.get('content-length')

        if total_length is None: # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                progress = int(100 * dl / total_length)
                bpy.context.window_manager.remi_ab_download_progress = progress/100   

    # Delete GPU drawing
    bpy.types.SpaceView3D.draw_handler_remove(handler3d, 'WINDOW')
    bpy.types.SpaceView3D.draw_handler_remove(handler2d, 'WINDOW')

@persistent
def remi_asset_browser_append(self, context):
    try:
        proxy_ob = bpy.context.object
        original_name = proxy_ob.name.split('|_RP#|')[0]
        condition = "|_RP#|" in proxy_ob.name and f"proxies/{original_name}" not in bpy.data.filepath
    except:
        condition = False

    if condition:
        # Add and delete handler
        bpy.app.handlers.depsgraph_update_post.append(remi_asset_browser_link)
        #Clear collection update handler
        for h in bpy.app.handlers.depsgraph_update_post:
            if h.__name__ == 'remi_asset_browser_append':
                bpy.app.handlers.depsgraph_update_post.remove(h)

        if bpy.context.window_manager.remi_ab_download_state == False:
            # Add the region OpenGL drawing callback
            handler3d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_3d, (), 'WINDOW', 'POST_VIEW')
            handler2d = bpy.types.SpaceView3D.draw_handler_add(draw_callback_2d, (), 'WINDOW', 'POST_PIXEL')

            # Set object pointer 
            bpy.context.window_manager.remi_ab_object_pointer = proxy_ob
            bpy.context.window_manager.remi_ab_download_progress = 0
        
            # Rename object
            proxy_ob.name = original_name

            # Request from firebase
            wm = bpy.context.window_manager
            wm.remi_ab_path_to_write = os.path.join(assets_browser_path, 'downloaded', f"{original_name}.blend")

            t1 = threading.Thread(target=download_asset, args=([
                    handler3d,
                    handler2d, 
                    f"https://remitriadi.org/assets/{original_name}.blend",
                ]))
            t1.daemon = True
            t1.start()
        else:
            # Download is running
            # Delete proxy object
            objs = bpy.data.objects
            objs.remove(objs[proxy_ob.name], do_unlink=True)
            report_info('Only one instance download is permitable at a time.')

@persistent
def remi_asset_browser_link(self,context):
    wm = bpy.context.window_manager
    condition = bpy.context.window_manager.remi_ab_download_progress == 1 and wm.remi_ab_path_to_write != '' and bpy.context.window_manager.remi_ab_download_state == True
    
    # Check if link object is there
    if condition:
        # Add and delete handler
        bpy.app.handlers.depsgraph_update_post.append(remi_asset_browser_append)
        #Clear collection update handler
        for h in bpy.app.handlers.depsgraph_update_post:
            if h.__name__ == 'remi_asset_browser_link':
                bpy.app.handlers.depsgraph_update_post.remove(h)

        downloaded_filepath = wm.remi_ab_path_to_write
        proxy_filepath = downloaded_filepath.replace('downloaded','proxies')
        inner_path = 'Object'

        full_name = os.path.basename(wm.remi_ab_path_to_write)
        file_name = os.path.splitext(full_name)
        object_name = file_name[0]
        proxy_ob = bpy.context.window_manager.remi_ab_object_pointer
        
        # Check if file path exists
        if(os.path.exists(downloaded_filepath)):
            # Reset the download before execute
            wm.remi_ab_path_to_write = ''
            bpy.context.window_manager.remi_ab_download_progress = 0
            bpy.context.window_manager.remi_ab_download_state = False

            # Delete file in proxy folder
            if os.path.exists(proxy_filepath):
                os.remove(proxy_filepath)

            #Link Object
            bpy.ops.wm.append(
                filepath=os.path.join(downloaded_filepath, inner_path, object_name),
                directory=os.path.join(downloaded_filepath, inner_path),
                filename=object_name
            )
            
            # Select active object
            ob = bpy.context.selected_objects[0]

            #Clear asset browser
            ob.asset_clear()

            # Change name ob to non-duplicate
            if('.001' in ob.name):
                ob.name = ob.name.replace('.001','')

            # Transform Matrix of object
            ob.matrix_world = proxy_ob.matrix_world

            # Delete proxy object
            objs = bpy.data.objects
            objs.remove(objs[proxy_ob.name], do_unlink=True)

            report_info('Successfully download file.')
    
def update_link_object_pointer(self,context):
    pass

def update_download_progress(self, context):
    pass

def update_percentage(self, context):
    pass




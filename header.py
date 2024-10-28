import bpy

class REMI_HD_Info_Message(bpy.types.Header):
    bl_label = "Custom Menu"
    bl_space_type = 'STATUSBAR'

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        message = wm.remi_re_info_message
        row = layout.row()
        row.operator('remi_re.report_info',text=f"  {message}   ", icon='INFO', translate=False)
        row.alignment = 'RIGHT'
        row.alert = True
        row.separator_spacer()   
        row.separator_spacer()   


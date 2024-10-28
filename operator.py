import bpy


class REMI_OT_Report_Info(bpy.types.Operator):
    """Report info placeholder."""
    bl_idname = 'remi_re.report_info'
    bl_label = 'Report Info'

    def execute(self, context):
        return {'FINISHED'}
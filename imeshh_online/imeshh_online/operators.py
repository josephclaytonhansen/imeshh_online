import bpy
from .manager import _manager

class SimpleOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "simple.move_to"
    bl_label = "Move "
    
    page: bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        return True

    @classmethod
    def description(cls, context,props):
        return f"Move to Page {props.page}"
    
    def execute(self, context):
        global _manager
        if _manager.current_page == self.page:
            return{'CANCELLED'}
        
        _manager.current_page = self.page
        _manager.get_assets()
        _manager.get_display_assets(self.page)
        return {'FINISHED'}

    # def invoke(self, context, event):
    #     manager.previous = manager.current_page
    #     return self.execute(context)

classes = [SimpleOperator]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

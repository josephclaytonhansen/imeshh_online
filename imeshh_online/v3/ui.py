import bpy
from .manager import _manager
class LayoutDemoPanel(bpy.types.Panel):
    """Creates a Panel in the scene context of the properties editor"""
    bl_label = "Layout Demo"
    bl_idname = "SCENE_PT_layout"
    bl_category = "ImeshhWeb"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        layout = self.layout

        # layout.label(text=_manager.categories[int(context.scene.imeshh_asset_type)]["name"])
        layout.prop(context.scene,"imeshh_asset_type",text="")
        row = layout.row()
        row.prop(context.scene,"imeshh_asset_category1",text="")
        if context.scene.imeshh_asset_category1 != "All assets":
            row.prop(context.scene,"imeshh_asset_category2",text="")

        row = layout.row()
        row.label(text=_manager.query_fetch_status.name)
        row.label(text=_manager.bgq_status.name)
        _manager.build_ui(layout,context)


classes = [LayoutDemoPanel]
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

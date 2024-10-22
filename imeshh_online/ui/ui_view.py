import bpy
from bpy.types import Panel
from .ui_main import IMESHH_main_panel
from ..functions import ADDON, enum_members_from_instance


class IMESHH_PT_view(IMESHH_main_panel, Panel):
    bl_label = "imeshh view panel"
    bl_options = {"DEFAULT_CLOSED"}

    def __init__(self) -> None:
        super().__init__()
        if not bpy.context.scene.imeshh_am.ui_folder_list:
            folder_list = bpy.context.scene.imeshh_am.ui_folder_list.add()
            folder_list.start_folder = bpy.context.scene.imeshh_am.ui_main_folder

    def draw(self, context):
        global ADDON
        layout = self.layout
        col = layout.column(heading="Local folders and files:")

        row = col.split()
        for item in enum_members_from_instance(context.scene.imeshh_am, "tabs"):
            row.prop_enum(context.scene.imeshh_am, "tabs", value=item, text="")
        row = col.row()
        row.prop(context.scene.imeshh_am, "ui_main_folder", text="Dirs")

        # Folder browsing
        row = col.row()
        for elem in context.scene.imeshh_am.ui_folder_list:
            row = col.row()
            row.prop(elem, "list_subdirs", text="Mds")

        # Search bar
        row = col.row()
        row.prop(context.scene.imeshh_am, "search_bar", text="", icon="VIEWZOOM")

        # Preview picker
        row = col.row()
        row.template_icon_view(
            context.window_manager,
            "asset_manager_previews",
            show_labels=True,
            scale_popup=context.preferences.addons[ADDON].preferences.scale_ui_popup,
        )
        # Object tab
        if context.scene.imeshh_am.tabs == "OBJECT":
            row = col.row(align=True)
            row.operator("imeshh.open_thumbnail", icon="FILE_IMAGE")
            row.operator("imeshh.open_blend", icon="FILE_BLEND")
            row = col.row(align=True)
            icon_snap = "SNAP_ON" if context.scene.imeshh_am.snap else "SNAP_OFF"
            row.prop(context.scene.imeshh_am, "snap", text="", icon=icon_snap)
            row.operator("imeshh.import_object", icon="APPEND_BLEND").link = False
            row.operator(
                "imeshh.import_object", icon="LINK_BLEND", text="Link Object"
            ).link = True
            row = col.row(align=True)
            row.operator("imeshh.import_material", icon="TEXTURE_DATA")
        # Material tab
        elif context.scene.imeshh_am.tabs == "MATERIAL":
            row = col.row()
            row.operator("imeshh.import_material", icon="TEXTURE_DATA")
        # HDRI tab
        elif context.scene.imeshh_am.tabs == "HDRI":
            row = col.row()
            row.operator("imeshh.import_hdr", icon="TEXTURE_DATA")
            row = layout.row()
            if (
                context.scene.world.node_tree
                and "GROUND_PROJECTION" in context.scene.world.node_tree.nodes
            ):
                col = layout.column(heading="Ground projection")
                for inp in context.scene.world.node_tree.nodes[
                    "GROUND_PROJECTION"
                ].inputs:
                    col.prop(inp, "default_value", text=inp.name)
            if (
                context.scene.world.node_tree
                and "HDRI_GROUP" in context.scene.world.node_tree.nodes
            ):
                col = layout.column(heading="HDRI")
                for inp in context.scene.world.node_tree.nodes["HDRI_GROUP"].inputs:
                    if inp.name != "HDRI":
                        col.prop(inp, "default_value", text=inp.name)

        col.row().separator(factor=3)
        box = col.box()
        row = box.row(align=True)
        row.operator("wm.url_open", text="Discord").url = (
            "https://discord.com/invite/3Wx85k75YR"
        )
        row.operator("wm.url_open", text="Learn Archviz").url = (
            "https://www.youtube.com/channel/UCYdjtG-RApzP7jMVzWQgJnQ/videos?view=0&sort=p&shelf_id=0"
        )
        row = box.row(align=True)
        box.operator("wm.url_open", text="imeshh.com").url = "https://imeshh.com/"


registry = [
    IMESHH_PT_view,
]

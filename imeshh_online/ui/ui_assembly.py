# Copyright (C) 2024 Aditia A. Pratama | aditia.ap@gmail.com
#
# This file is part of imeshh_am.
#
# imeshh_am is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# imeshh_am is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with imeshh_am.  If not, see <https://www.gnu.org/licenses/>.

import bpy
import os
import tempfile
from bpy.types import Panel
from .ui_main import IMESHH_main_panel

from .. import functions as fn
from ..props import preview_collections


class IMESHH_PT_assembly(IMESHH_main_panel, Panel):
    """! Panel for web interation with iMesh website

    Loads the 3D models using the REST webservice from the WordPress plugin.

    Models load from the link
    /wp-json/blender_api/imeshhs

    Categories from
    /wp-json/blender_api/imeshh_categories

    """

    bl_label = "iMeshh Assembly"

    def __init__(self) -> None:
        """! Init the Panel
        Loads default Blender Panel initialization and if does not exist a folder list add a default.
        For web it is ui_web_folder.
        See imeshh_am.utils.iMeshh_AM class.
        """
        super().__init__()
        if not bpy.context.scene.imeshh_am.ui_web_list:
            folder_list = bpy.context.scene.imeshh_am.ui_web_list.add()
            folder_list.start_folder = bpy.context.scene.imeshh_am.ui_web_categories

    # Draw the panel
    def draw(self, context):
        global ADDON
        layout = self.layout
        col = layout.column(heading="Shop from iMeshh website:")

        row = col.split()
        for item in fn.enum_members_from_instance(context.scene.imeshh_am, "downloads"):
            row.prop_enum(context.scene.imeshh_am, "downloads", value=item, text="")
        row = col.row()
        # col.row().separator(factor=3)
        prefs = bpy.context.preferences.addons[fn.ADDON].preferences
        if prefs.default_folder == str(tempfile.gettempdir()):
            box = col.box()
            col = box.column_flow(columns=0, align=True)
            col.alert = True
            col.label(text="Please set your Default", icon="FILEBROWSER")
            col.label(text="Folder in User Preferences", icon="BLANK1")

        previews = context.window_manager.asset_manager_previews
        downloading = bpy.context.scene.imeshh_am.downloading
        if previews:
            row.template_icon_view(
                context.window_manager,
                "asset_manager_previews",
                show_labels=True,
                scale_popup=context.preferences.addons[
                    fn.ADDON
                ].preferences.scale_ui_popup,
            )
            box = col.box()
            row = box.row(align=True)
            selected = int(previews)
            item = preview_collections["web"].my_previews_data[selected]
            text = (
                "Download"
                # if not os.path.exists(fn.zipfilepath(item))
                if not downloading
                else "Downloading..."
                # else "Downloading..." if downloading else "Append"
            )
            row.active = False if downloading else True
            row.operator("object.imeshh_download", text=text)
        else:
            row.scale_y = 2
            row.alert = True
            row.operator("object.imeshh_download", text="Please wait...")


registry = [
    IMESHH_PT_assembly,
]

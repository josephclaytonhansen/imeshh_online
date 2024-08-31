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
from bpy.types import Panel
from .ui_main import IMESHH_main_panel
from ..auth import auth_file_exists


class IMESHH_PT_settings(IMESHH_main_panel, Panel):
    bl_label = "imeshh settings panel"
    bl_options = {"DEFAULT_CLOSED"}

    # Draw the panel
    @classmethod
    def poll(cls, context):
        return auth_file_exists()

    def draw(self, context):
        layout = self.layout
        col = layout.column(heading="Linked Object Settings")
        col.prop(context.scene.imeshh_am, "asset_manager_collection_import")
        col.prop(context.scene.imeshh_am, "asset_manager_auto_rename")

        col = layout.column(heading="Camera Settings")
        col.prop(context.scene.imeshh_am, "asset_manager_ignore_camera")

        col = layout.column(heading="Web Settings")
        col.prop(
            context.scene.imeshh_am, "the_im_url", icon="ASSET_MANAGER", text="URL"
        )


registry = [
    IMESHH_PT_settings,
]

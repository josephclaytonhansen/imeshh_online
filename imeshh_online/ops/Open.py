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
from bpy.types import Operator
from bpy import app
from ..props import CURR_PREVIEW, preview_collections
from ..functions import get_selected_file, get_selected_blend
import os
import sys
import webbrowser
import subprocess


class IMESHH_OT_open_thumbnail(Operator):
    """Open the thumbnail image"""

    bl_idname = "imeshh.open_thumbnail"
    bl_label = "Thumbnail"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        filepath = get_selected_file(context)
        items = CURR_PREVIEW

        for item in items:
            if item[0] == filepath:
                icon_id = item[3]
                for preview_path, preview_image in preview_collections["main"].items():
                    if icon_id == preview_image.icon_id and preview_path.endswith(
                        (".png", ".jpg")
                    ):
                        webbrowser.open(preview_path)

        return {"FINISHED"}


class IMESHH_OT_open_blend(Operator):
    """Open the .blend file for the asset"""

    bl_idname = "imeshh.open_blend"
    bl_label = ".blend"
    bl_options = {"REGISTER", "UNDO"}

    def open_blend(self, binary, filepath):
        if sys.platform.startswith("win"):
            base, exe = os.path.split(binary)
            subprocess.Popen(["start", "/d", base, exe, filepath], shell=True)
        else:
            subprocess.Popen([binary, filepath])

    def execute(self, context):
        selected_blend = get_selected_blend(context)
        self.open_blend(app.binary_path, selected_blend)
        return {"FINISHED"}


registry = [
    IMESHH_OT_open_thumbnail,
    IMESHH_OT_open_blend,
]
